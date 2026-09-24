# DataSage — Architecture

## Overview

DataSage is a multi-agent AI system that analyses tabular data through a sequential pipeline of specialised LLM agents, orchestrated by LangGraph. The system follows a **supervisor-router pattern** where a central supervisor reads shared state and deterministically routes execution to the correct agent at each step.

---

## Agent Pipeline
```
                ┌─────────────────────────────────┐
                │           SUPERVISOR             │
                │   reads state → decides next     │
                └──┬──────┬──────┬──────┬─────────┘
                   │      │      │      │
               inspect  clean   eda  reporter
                   │      │      │      │
                   ▼      ▼      ▼      ▼
               Inspector Cleaner EDA  Reporter
                                        │
                                     followup Q&A
                                        │
                                       end
```


### Routing Rules (Supervisor)

The supervisor runs before every node and checks state to decide the next agent:

| Condition | Next Agent |
|---|---|
| `data_domain == ""` | `inspect` |
| `quality_score == 0` | `inspect` |
| `cleaning_report == {}` | `cleaner` |
| `analysis_results == {}` | `eda` |
| `report == ""` | `reporter` |
| `current_question != ""` | `reporter` (Q&A mode) |
| everything complete | `end` |

---

## Shared State

All agents communicate through a single `AgentState` TypedDict passed through the LangGraph graph. No agent calls another directly — they read from state, write to state, and return.

```python
class AgentState(TypedDict):
    # Raw + cleaned dataframes
    raw_df, cleaned_df

    # Inspector outputs
    column_names, data_types, null_counts, row_count,
    column_count, sample_values, quality_score,
    issues_found, data_domain

    # Cleaner outputs
    cleaning_report

    # EDA outputs
    analysis_results, key_findings, visualisations

    # Reporter outputs
    report

    # Q&A
    conversation_history, current_question,
    question_type, followup_answer

    # Supervisor internal
    next_agent, instructions, iteration_count

    # Meta
    user_id, upload_id, error, status
```

---

## Agent Details

### Inspector
- Reads `raw_df` column names, dtypes, null counts, and sample values
- Sends a structured prompt to Gemini to detect `data_domain` and `quality_score`
- Writes: `column_names`, `data_types`, `null_counts`, `sample_values`, `row_count`, `column_count`, `quality_score`, `issues_found`, `data_domain`

### Cleaner
- Reads inspector outputs and asks Gemini for a pandas cleaning plan
- Gemini returns executable Python code operating on a variable called `df`
- `execute_with_retry` runs the code in a restricted namespace; on failure, feeds the error back to Gemini and retries (max 3 attempts)
- Writes: `cleaned_df`, `cleaning_report`

### EDA Agent
- Runs `compute_stats()` — descriptive stats via pandas (no LLM)
- Calls Gemini with stats to generate `key_findings` (natural language bullet points)
- Calls Gemini with column metadata to generate `visualisations` (list of chart spec dicts)
- Chart spec format: `{chart_type, x_column, y_column, title}`
- Writes: `analysis_results`, `key_findings`, `visualisations`

### Reporter
- **Report mode** (`question_type != "followup"`): builds full Markdown report from domain, quality, findings, cleaning report, and stats
- **Q&A mode** (`question_type == "followup"`): answers `current_question` using the full conversation history as context; appends to `conversation_history`
- Writes: `report`, `followup_answer`, `conversation_history`

---

## Tool Layer

Tools are stateless utility functions called by agents or `write_full_report`. They are not LangGraph nodes.

| Tool | Called By | Purpose |
|---|---|---|
| `code_executor.py` | Cleaner | Execute LLM-generated pandas code safely |
| `chart_generator.py` | `report_writer` | Turn chart specs → Plotly figures → JSON |
| `db_writer.py` | `report_writer` | Save run, report, charts, conversations to PostgreSQL |
| `report_writer.py` | `02_analysis.py` | Orchestrate chart gen + all DB saves after graph completes |

---

## Data Flow
```
User uploads file (01_upload.py)
│
▼
file_parser.parse_file() → DataFrame
file_parser.handle_upload() → saves User + Upload to DB
│
▼
02_analysis.py builds initial AgentState
│
▼
graph.invoke(state)
└─ Supervisor → Inspector writes quality + domain
└─ Supervisor → Cleaner writes cleaned_df
└─ Supervisor → EDA writes findings + chart specs
└─ Supervisor → Reporter writes report text
└─ Supervisor → END
│
▼
write_full_report(result)
├─ generate_all_charts() → Plotly JSON per spec
├─ save_analysis_run() → AnalysisRun row
├─ save_report() → Report row
└─ save_visualisations() → Visualisations rows
│
▼
02_analysis.py renders Report / Charts / Q&A tabs
```



---

## LLM Usage

All LLM calls go through `core/llm_utils.py` which wraps Gemini with `_llm_with_retry` — exponential backoff on rate limit errors. The model used is `gemini-1.5-flash` (fast + cheap for repeated calls).

LLM is used for:
- Domain detection and quality scoring (Inspector)
- Generating pandas cleaning code (Cleaner)
- Generating natural language key findings (EDA)
- Generating chart specs as structured JSON (EDA)
- Writing the narrative report (Reporter)
- Answering follow-up questions (Reporter Q&A)

---

## Error Handling Strategy

| Layer | Strategy |
|---|---|
| LLM calls | `_llm_with_retry` — 3 retries with backoff |
| Cleaning code | `execute_with_retry` — 3 retries, error fed back to LLM |
| Chart generation | Per-chart try/except, logs warning and skips bad spec |
| Agent errors | Caught in `02_analysis.py`, written to `state["error"]`, shown in UI |
| DB writes | Rollback on exception, re-raise with logger |