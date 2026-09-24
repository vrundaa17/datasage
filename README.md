# DataSage 🔍

> An AI-powered multi-agent data analyst built with LangGraph, Google Gemini, and Streamlit.

Upload any CSV or Excel file and DataSage automatically inspects, cleans, analyses, and reports on your data — then lets you ask follow-up questions in plain English.

---

## Features

- **Automatic domain detection** — real estate, finance, HR, sales, and more
- **Self-healing data cleaning** — LLM generates pandas code and retries on failure (up to 3x)
- **EDA with chart generation** — bar, line, scatter, histogram, box, pie, heatmap via Plotly
- **Narrative report** — structured Markdown report with key findings and recommendations
- **Conversational Q&A** — ask follow-up questions about your data after analysis
- **Full persistence** — every run, report, chart, and conversation saved to PostgreSQL
- **Analysis history** — browse and revisit past runs

---

## Architecture

DataSage uses a **LangGraph supervisor pattern** — a central supervisor agent routes work to specialised agents in a deterministic pipeline:
```
Upload → Inspector → Cleaner → EDA → Reporter → End
                                        ↕
                                        Q&A (followup)
```


### Agents

| Agent | Responsibility |
|---|---|
| **Supervisor** | Reads state, decides next agent, routes graph |
| **Inspector** | Detects domain, scores data quality, flags null/type issues |
| **Cleaner** | LLM generates pandas cleaning code, `execute_with_retry` self-corrects |
| **EDA** | Computes statistics, generates key findings and chart specs via LLM |
| **Reporter** | Builds full Markdown report, answers follow-up Q&A questions |

### Tech Stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph 1.2 |
| LLM | Google Gemini 1.5 Flash (via `langchain-google-genai`) |
| Frontend | Streamlit 1.64 |
| Charts | Plotly 7 |
| Database | PostgreSQL + SQLAlchemy 2 |
| File parsing | pandas (CSV / xlsx / xls) |

---

## Project Structure

```
datasage/
├── agents/
│ ├── state.py # AgentState TypedDict — shared across all agents
│ ├── supervisor.py # Routing logic
│ ├── inspector.py # Data quality + domain detection
│ ├── cleaner.py # LLM-driven data cleaning with retry
│ ├── eda.py # Statistics, findings, chart specs
│ ├── reporter.py # Report generation + Q&A
│ └── graph.py # LangGraph graph definition
│
├── app/
│ ├── main.py # Streamlit home page
│ ├── components/
│ │ ├── session.py # Session token management
│ │ ├── charts.py # Plotly chart rendering
│ │ ├── chat.py # Conversational Q&A UI
│ │ └── report_card.py# Report + findings display
│ └── pages/
│ ├── 01_upload.py # File upload page
│ ├── 02_analysis.py# Pipeline runner + results (tabs)
│ ├── 03_report.py # Standalone report view
│ └── 04_history.py # Past analysis runs
│
├── core/
│ ├── config.py # Environment config + model names
│ ├── logger.py # Structured logging setup
│ └── exce.py # Custom exceptions
│
├── db/
│ ├── connection.py # SQLAlchemy engine + session
│ └── models.py # ORM models (7 tables)
│
├── services/
│ └── file_parser.py # File parsing, user creation, upload saving
│
├── tools/
│ ├── chart_generator.py# Plotly chart generation from specs
│ ├── code_executor.py # Safe pandas code execution with retry
│ ├── db_writer.py # Save runs, reports, visualisations, messages
│ └── report_writer.py # Orchestrates chart gen + all DB saves
│
├── tests/
│ ├── test_inspector.py
│ ├── test_cleaner.py
│ ├── test_eda.py
│ ├── test_till_eda.py
│ └── test_full.py # Full pipeline + Q&A end-to-end test
│
├── .env
├── requirements.txt
└── README.md

```


---

## Database Schema
```
users — session-based identity
uploads — file metadata per user
analysis_runs — one row per pipeline execution
reports — Markdown report text + recommendations
visualisations — Plotly JSON per chart per run
conversations — Q&A session per run
messages — individual Q&A messages (role + content)
```


---

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL (running locally or remote)
- Google Gemini API key

### 1. Clone and install

```bash
git clone https://github.com/yourname/datasage.git
cd datasage
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/datasage
APP_ENV=development
LOG_LEVEL=INFO
```

### 3. Create database tables

```bash
python db/models.py
```

### 4. Run the app

```bash
streamlit run app/main.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Usage

1. **Upload** — go to the Upload page, choose a CSV or Excel file, click **Start Analysis**
2. **Analysis** — the pipeline runs automatically (inspect → clean → EDA → report), takes ~10–20s
3. **Report tab** — view data quality score, key findings, and the full narrative report
4. **Charts tab** — browse all auto-generated Plotly visualisations
5. **Ask Questions tab** — type any question about your data in plain English
6. **History** — revisit any past analysis from the History page

---

## Running Tests

```bash
# Individual agent tests
python -m pytest tests/test_inspector.py -v
python -m pytest tests/test_cleaner.py -v
python -m pytest tests/test_eda.py -v

# Full pipeline end-to-end
python -m pytest tests/test_full.py -v
```

---

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key | ✅ |
| `DATABASE_URL` | PostgreSQL connection string | ✅ |
| `APP_ENV` | `development` or `production` | ❌ (default: `development`) |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING` | ❌ (default: `INFO`) |

---

## Known Limitations

- Single-user session model (no auth system — users are identified by a UUID session token)
- Large files (>50MB) are rejected at upload
- Chart specs are LLM-generated and occasionally suggest columns that don't exist (handled gracefully with a warning log)
- Q&A context is limited to the current browser session

---
