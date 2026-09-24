from langchain_google_genai import ChatGoogleGenerativeAI
from agents.state import AgentState
from core.config import config
from core.logger import get_logger
from tools.code_executor import _llm_with_retry
import json,traceback

logger= get_logger(__name__)

def build_report(state : AgentState,llm)->AgentState:
    domain = state.get("data_domain", "unknown")
    key_findings = state.get("key_findings", [])
    analysis= state.get("analysis_results", {})
    cleaning = state.get("cleaning_report", {})
    visualisations= state.get("visualisations", {})
    quality_score= state.get("quality_score", {})
    issues_found= state.get("issues_found", {})
    
    shape =analysis.get("shape", {})

    numeric_cols = analysis.get("numeric_columns", [])   
    cat_cols= analysis.get("categorical_columns", []) 
    datetime_cols = analysis.get("datetime_columns", [])  
    stats=analysis.get("stats", {})
    
    chart_summary = []
    for v in visualisations:
        chart_summary.append(
            f"- {v.get('chart_type','').upper()}: {v.get('title','')} | {v.get('reason','')}"
        )

    cleaning_actions = cleaning.get("actions_taken",[])
    cleaning_reasoning = cleaning.get("llm_reasoning", "")

    prompt = f"""
        You are a senior data analyst writing a professional analysis report.

        Dataset Info:
        - Domain: {domain}
        - Shape: {shape.get('rows', '?')} rows x {shape.get('columns', '?')} columns
        - Quality Score (after cleaning): {quality_score}%
        - Numeric columns: {numeric_cols}
        - Categorical columns: {cat_cols}
        - Datetime columns : {datetime_cols}
        - Issues originally found: {issues_found}

        Cleaning Summary:
        - Actions taken: {json.dumps(cleaning_actions, indent=2)}
        - Reasoning: {cleaning_reasoning}

        Key Findings from EDA: {json.dumps(key_findings, indent=2)}
        Numeric Statistics Summary: {json.dumps(stats.get('numeric_summary', {}), indent=2, default=str)}
        Visualisations Recommended : {chr(10).join(chart_summary) if chart_summary else 'None'}

        Write a professional analysis report in clean Markdown. Structure it exactly like this:
        
        # DataSage Analysis Report

        ## 1. Dataset Overview
        (describe the dataset: domain, size, column types, overall quality)

        ## 2. Data Quality & Cleaning
        (what issues were found, what was cleaned, final quality score)

        ## 3. Key Findings
        (expand on each finding with context not just a bullet dump)

        ## 4. Statistical Highlights
        (mention standout stats, correlations, skewness only the meaningful ones)

        ## 5. Visualisation Recommendations
        (list the charts and explain what each reveals)

        ## 6. Recommendations & Next Steps
        (actionable recommendations based on the data and domain)

        ---
        
        Rules:
        - Be specific : use actual column names and numbers
        - Keep it professional but readable
        - Do NOT mention that you are an AI
        - Do NOT include any code blocks
        - Target length: 500-800 words
        
    """
    return _llm_with_retry(llm, prompt)
    
    
def answer_question(state: AgentState, llm):
    question = state.get("current_question", "")
    domain = state.get("data_domain", "unknown")
    key_findings = state.get("key_findings", [])
    analysis= state.get("analysis_results", {})
    stats = analysis.get("stats", {})
    conversation= state.get("conversation_history", [])
    
    history_text=''
    if conversation:
        history_text = "\n".join(
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in conversation[-6:]
        )
    prompt =f""" 
        You are a data analyst assistant. Answer the user's question using the analysis data below.
        Domain: {domain}
        Key Findings: {json.dumps(key_findings, indent=2)}
        Statistics: {json.dumps(stats.get('numeric_summary', {}), indent=2, default=str)}=
        Categorical Summary: {json.dumps(stats.get('categorical_summary', {}), indent=2, default=str)}

        {f"Conversation History:{chr(10)}{history_text}" if history_text else ""}

        User Question: {question}

        Rules:
        - Answer directly and concisely
        - Use actual numbers and column names from the data
        - If the answer isn't in the data, say so clearly
        - Keep response under 200 words
        - No code blocks, no markdown headers
    """
    return _llm_with_retry(llm, prompt)


def reporter_node(state: AgentState)-> AgentState:
    logger.info("[ REPORTER ] agent started")

    try:
        llm = ChatGoogleGenerativeAI( model=config.FLASH_MODEL,google_api_key=config.GEMINI_API_KEY )
        question_type = state.get("question_type", "")
        if question_type in ("followup", "question") and state.get("current_question"):
            logger.info(f"Q&A mode — answering: {state.get('current_question')}")
            answer = answer_question(state, llm)
            history = list(state.get("conversation_history") or [])
            history.append({"role": "user","content": state["current_question"]})
            history.append({"role": "assistant", "content": answer})

            logger.info("[ REPORTER ] Q&A answer generated")
            return {
                **state,
                "followup_answer": answer,
                "conversation_history": history,
                "current_question": "",
                "question_type": "",
                "next_agent": "supervisor",
                "status":"completed",
            }
            
        report = build_report(state, llm)
        logger.info("[ REPORTER ] report generated successfully")
        return {
            **state,
            "report": report,
            "next_agent":"supervisor",
            "status": "completed",
        }
    except Exception as e:
        logger.error(f"[ REPORTER ] failed: {e}")
        logger.error(traceback.format_exc())
        return {**state, "error": str(e), "status": "failed"}
    pass