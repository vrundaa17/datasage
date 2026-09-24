from langchain_google_genai import ChatGoogleGenerativeAI
from agents.state import AgentState
from core.config import config
from core.logger import get_logger
from tools.code_executor import _llm_with_retry
import json,re,traceback

logger= get_logger(__name__)




def compute_stats(df):
    stats = {}
    
    numeric_df = df.select_dtypes(include='number')
    if not numeric_df.empty:
        stats['numeric_summary']= json.loads(numeric_df.describe().round(4).to_json())
        if len(numeric_df.columns) >1:
            stats['correlations']=json.loads(numeric_df.corr().round(4).to_json())
        else:
            stats['correlations']={}
        stats["skewness"] = numeric_df.skew().round(4).to_dict()
    else:
        stats['correlations']={}
        stats['numeric_summary']={}
        stats['skewness']={}
    
    
    cat_df = df.select_dtypes(include=['object','category'])
    stats['categorical_summary']={}
    for col in cat_df.columns:
        value_counts = df[col].value_counts()
        counts = value_counts.sample(min(10, len(value_counts)))
        stats['categorical_summary'][col]= counts.to_dict()
        
    datetime_cols =df.select_dtypes(include=["datetime", "datetimetz",'datetime64'])
    if not datetime_cols.empty:
        stats["datetime_range"] = {}
        for col in datetime_cols:
            stats["datetime_range"][col] = {
                "min": str(df[col].min()),
                "max": str(df[col].max()),
            }
                
    stats["shape"] = {"rows": len(df), "columns": len(df.columns)}
    stats["null_summary"] = df.isnull().sum().to_dict()
    stats["column_types"] = {col: str(dtype) for col, dtype in df.dtypes.items()}

    return stats


def get_findings(stats, domain, columns, llm):
    prompt = f"""
        You are a senior data analyst. Analyse these statistics and write key findings.

        Domain: {domain}
        Columns: {columns}

        Statistics:
        {json.dumps(stats, indent=2, default=str)}
        
        Write 5-7 key findings as a JSON array of strings.
        Each finding should be:
        - Specific (mention actual column names and numbers)
        - Meaningful for the {domain} domain
        - Actionable or insightful, not just restating numbers

        Return ONLY a valid JSON array. No explanation, no markdown, no backticks.
        Example format: ["Finding 1...", "Finding 2...", ...]

    """
    raw = _llm_with_retry(llm, prompt)
    raw = re.sub(r'^```(?:json)?\s*', '', raw.strip())
    raw = re.sub(r'\s*```$', '', raw.strip())
    
    try:
        findings = json.loads(raw)
        if isinstance(findings, list):
            return [str(f) for f in findings]
        return [str(findings)]
    except json.JSONDecodeError:
        logger.warning("Could not parse findings as JSON")
        return [raw]


def get_chart(df, domain, stats,llm):
    col_info = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        n_unique = df[col].nunique()
        col_info.append(f"{col} | {dtype} | {n_unique} unique values")

    prompt =f"""
        You are a data visualisation expert. Decide which charts best represent this dataset.

        Domain: {domain}
        Shape: {df.shape[0]} rows x {df.shape[1]} columns

        Columns:
        {chr(10).join(col_info)}

        Numeric correlations (if any):
        {json.dumps(stats.get('correlations', {}), indent=2)}

        Return ONLY a valid JSON array of chart specs. No explanation, no markdown, no backticks.
        Each spec must follow this exact structure:
        [
        {{
            "chart_type": "bar|line|scatter|histogram|heatmap|pie|box",
            "x_column": "column_name or null",
            "y_column": "column_name or null",
            "title": "descriptive chart title",
            "reason": "why this chart is useful for this dataset"
        }}
        ]

        Rules:
        - Max 5 charts - pick only the most insightful ones
        - Use column names that actually exist in the dataset
        - For time series data, use line charts with datetime on x axis
        - For correlations between two numerics, use scatter
        - For distributions, use histogram or box
        - For categorical breakdowns, use bar or pie (pie only if <6 categories)
        - For correlation matrix, use heatmap
    """
    raw = _llm_with_retry(llm, prompt)
    raw = re.sub(r'^```(?:json)?\s*', '', raw.strip())
    raw = re.sub(r'\s*```$', '', raw.strip())
    
    try:
        specs = json.loads(raw)
        if isinstance(specs, list):
            valid_specs = []
            required_keys = {"chart_type", "title"}
            for spec in specs:
                if isinstance(spec, dict) and required_keys.issubset(spec.keys()):
                    valid_specs.append(spec)
                else:
                    logger.warning(f"Skipping invalid chart spec: {spec}")
            return valid_specs
        return []
    except json.JSONDecodeError:
        logger.warning("Could not parse chart specs as JSON, returning empty list")
        return []
    
    
    
def eda_node(state: AgentState):
    logger.info("[ EDA ] agent started")
    
    df = state.get("cleaned_df")
    if df is None:
        logger.warning("No cleaned_df found, falling back to raw_df")
        df = state.get("raw_df")
        
    if df is None or len(df) == 0:
        logger.error("No dataframe available for EDA")
        return {
            **state,
            "error": "No dataframe available for EDA",
            "status": "failed"
        }
    try:
        domain = state.get("data_domain","unknown")
        llm = ChatGoogleGenerativeAI(
            model=config.FLASH_MODEL,
            google_api_key=config.GEMINI_API_KEY
        )
        logger.info(f"Computing statistics on {df.shape[0]}x{df.shape[1]} dataframe...")
        stats = compute_stats(df)
        logger.info("Statistics computed")
        
        logger.info("Generating key findings...")
        key_findings = get_findings(stats=stats, llm=llm, domain=domain,columns=list(df.columns))
        
        logger.info("Generating chart specs...")
        visualisations = get_chart(df=df,domain=domain,stats=stats,llm=llm)
        
        analysis_results = {
            "stats": stats,
            "domain": domain,
            "shape": stats["shape"],
            "numeric_columns": list(df.select_dtypes(include="number").columns),
            "categorical_columns": list(df.select_dtypes(include=["object", "category"]).columns),
            "datetime_columns": list(df.select_dtypes(include=["datetime64"]).columns),
        }

        logger.info(f"EDA completed. | Findings : {len(key_findings)} | Charts : {len(visualisations)}")
        
        return {
            **state,
            "analysis_results": analysis_results,
            "key_findings": key_findings,
            "visualisations": visualisations,
            "next_agent": "supervisor",
            "status" : "running"
        }
    except Exception as e:

        logger.error(f"[ EDA ] failed: {e}")
        logger.error(traceback.format_exc())
        return {**state, "error": str(e), "status": "failed"}