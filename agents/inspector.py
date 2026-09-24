# import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from agents.state import AgentState
from tools.code_executor import execute_code
from core.config import config
from core.logger import get_logger
import traceback

logger = get_logger(__name__)


def inspect_node(state: AgentState) -> AgentState:
   
    logger.info("Inspector agent started")
    
    llm = ChatGoogleGenerativeAI(
        model=config.FLASH_MODEL,
        google_api_key=config.GEMINI_API_KEY,
    )
    
    df = state["raw_df"]
    
    try:
        # Basic stats via pandas directly
        column_names = list(df.columns)
        data_types = {col: str(dtype) 
                      for col, dtype in df.dtypes.items()}
        null_counts = df.isnull().sum().to_dict()
        null_counts = {k: int(v) 
                       for k, v in null_counts.items()}
        row_count = len(df)
        column_count = len(df.columns)
        sample_values = df.head(3).to_dict()
        
        # Quality score
        total_cells = row_count * column_count
        null_cells = df.isnull().sum().sum()
        quality_score = round(
            ((total_cells - null_cells) / total_cells) * 100, 2
        )
        
        
        issues = []
        for col in df.columns:
            null_pct = (df[col].isnull().sum() / row_count) * 100
            if null_pct > 50:
                issues.append(
                    f"{col} has {null_pct:.1f}% missing values"
                )
            if null_pct > 0 and null_pct <= 50:
                issues.append(
                    f"{col} has {null_pct:.1f}% nulls"
                )
        
        if df.duplicated().sum() > 0:
            issues.append(
                f"{df.duplicated().sum()} duplicate rows found"
            )
        
        # Ask LLM to identify data domain
        summary = f"""
        Columns: {column_names}
        Data types: {data_types}
        Sample values: {df.head(2).to_string()}
        """
        
        domain_prompt = f"""
        Based on these columns and sample data,
        what domain is this data from?
        
        {summary}
        
        Reply with exactly one word:
        sales / customer / health / finance / inventory / unknown
        """
        
        domain_response = llm.invoke(domain_prompt)
        content = domain_response.content

        if isinstance(content, list):
            content = "".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in content
            )

        data_domain = content.strip().lower()

        
        logger.info(f"Inspector complete. Domain: {data_domain} | Quality: {quality_score}%"
        )
        
        return {
            **state,
            "column_names": column_names,
            "data_types": data_types,
            "null_counts": null_counts,
            "row_count": row_count,
            "column_count": column_count,
            "sample_values": sample_values,
            "data_domain": data_domain,
            "quality_score": quality_score,
            "issues_found": issues,
            "next_agent": "supervisor",
            "status": "running"
        }
    
    except Exception as e:
        logger.error(f"Inspector failed: {e}")
        logger.error(traceback.format_exc())
        return {
            **state,
            "error": str(e),
            "status": "failed"
        }