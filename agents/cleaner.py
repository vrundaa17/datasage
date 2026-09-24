import pandas as pd
import json,traceback,re
from langchain_google_genai import ChatGoogleGenerativeAI
from agents.state import AgentState
from core.config import config
from core.logger import get_logger

logger = get_logger(__name__)

def ask_cleanup_plan(issues, df, domain,llm):
    col_info=[]
    row_count= len(df)
    
    for col in df.columns:
        null_pct = round(df[col].isnull().sum() / row_count * 100, 1)
        dtype = str(df[col].dtype)
        sample = df[col].dropna().head(3).tolist()
        col_info.append({
            "name": col,
            "dtype": dtype,
            "null_pct": null_pct,
            "sample_values": sample
        })
        
    clean_prompt= f"""
        You are a data cleaning expert. Analyse this dataset and return a cleaning plan.

        Domain: {domain}
        Total rows: {row_count}
        Issues found: {issues}

        Columns: {json.dumps(col_info, indent=2, default=str)}
        Return ONLY a valid JSON object with this exact structure, no explanation, no markdown:
        {{
        "columns_to_drop": [
            {{"name": "col_name", "reason": "why drop this"}}
        ],
        "columns_to_impute": [
            {{"name": "col_name", "strategy": "median|mode|constant", "value": null, "reason": "why"}}
        ],
        "columns_to_rename": [
            {{"original": "old name", "new": "new_name", "reason": "why"}}
        ],
        "columns_to_cast": [
            {{"name": "col_name", "to_type": "numeric|datetime|string", "reason": "why"}}
        ],
        "drop_duplicates": true,
        "reasoning": "2-3 sentences explaining overall cleaning strategy for this specific dataset"
        }}

        Rules for your decisions:
        - Drop a column only if it has >80% nulls AND is not a meaningful outcome/target column
        - If a column is an outcome that gets filled in later (like actual results, final values), do NOT drop it leave it as is
        - For numeric nulls under 50%: use median (robust to outliers)
        - For categorical nulls under 50%: use mode
        - Rename columns that have special characters, spaces, or currency symbols
        - Cast columns that look numeric but are stored as strings
        - Think about the domain, a finance column with 30% nulls may be intentional (pending transactions)
        """
    
        
    response = llm.invoke(clean_prompt)
    content = response.content
    if isinstance(content, list):
        content = "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in content
        )

    raw = content.strip().lower()

    try :
        plan = json.loads(raw)
        
    except json.JSONDecodeError as e:
        logger.error("[ CLEANER - PLAN ] invalid JSON")
        logger.warning(f"Raw response was: {raw[:500]}")
        plan = {
            "columns_to_drop": [],
            "columns_to_impute": [],
            "columns_to_rename": [],
            "columns_to_cast": [],
            "drop_duplicates": True,
            "reasoning": "Invalid LLM JSON"
        }

    return plan


def execute_plan(df, plan):
    actions = []
            
    # --
    auto_rename = {}
    for col in df.columns:
        clean = re.sub(r'[^\w\s]', '', col)    
        clean = re.sub(r'\s+', '_', clean)       
        clean = clean.lower().strip('_')       
        clean = re.sub(r'_+', '_', clean)      
        if clean != col and clean:
            auto_rename[col] = clean
    if auto_rename:
        df = df.rename(columns=auto_rename)
        for old, new in auto_rename.items():
            actions.append(f"Renamed {old} | {new}")

    rename_map = {}
    for item in plan.get("columns_to_rename", []):
        original = auto_rename.get(item.get("original"), item.get("original"))
        new_name = item.get("new")
        if original in df.columns and new_name:
            new_name = re.sub(r'[^\w]', '_', new_name).lower().strip('_')
            if new_name != original:
                rename_map[original] = new_name
                actions.append(f"Renamed {original} | {new_name} : {item.get('reason', '')}")
    if rename_map:
        df = df.rename(columns=rename_map)
        
    # -- 
    for item in plan.get("columns_to_drop",[]):
        col = item.get("name")
        col = rename_map.get(col, col)
        if col in df.columns:
            df = df.drop(columns=[col])
            actions.append(f"Dropped column '{col}': {item.get('reason', '')}")
            
            
    #--
    for item in plan.get("columns_to_cast", []):
        col = rename_map.get(item.get("name"), item.get("name"))
        to_type = item.get("to_type")
        if col not in df.columns:
            continue
        try:
            if to_type =="numeric":
                df[col] = pd.to_numeric(df[col], errors='coerce')
                actions.append(f"Cast {col} to numeric")
                
            elif to_type=="datetime":
                df[col]= pd.to_datetime(df[col] , errors='coerce')
                actions.append(f"Cast {col} to datetime")
            elif to_type=='string':
                df[col] = df[col].astype(str)
                actions.append(f"Cast {col} to string")
        except Exception as e:
            logger.warning(f"Could not cast {col} - {to_type} : {e}")
    
    #--
    if plan.get("drop_duplicates", False):
        before = len(df)
        df = df.drop_duplicates()
        dropped = before - len(df)
        if dropped > 0:
            actions.append(f"Dropped {dropped} duplicate rows")
            
    #-- 
    for item in plan.get("columns_to_impute", []):
        col = rename_map.get(item.get("name"), item.get("name"))
        strategy = item.get("strategy", "median")
        if col not in df.columns:
            continue
        null_count = df[col].isnull().sum()
        if null_count == 0:
            continue
        try:
            if strategy =="median":
                fill_val = df[col].median()
                df[col] = df[col].fillna(fill_val)
                actions.append(f"Imputed {col} | median | {fill_val}")
            elif strategy =="mode":
                mode_val = df[col].mode()
                if not mode_val.empty:
                    fill_val = mode_val[0]
                    df[col]=df[col].fillna(fill_val)
                    actions.append(f"Imputed {col} | mode | {fill_val}")
            elif strategy =='constant':
                fill_val = item.get("value", 0)
                df[col] = df[col].fillna(fill_val)
                actions.append(f"Imputed {col} | constant | {fill_val}")
                
        except Exception as e:
            logger.warning(f"Could not impute {col} : {e}")
    
    return df, actions  
    
    

def clean_node(state: AgentState):
    logger.info("[ CLEANER ] agent started")
    df = state["raw_df"].copy()
    
    try:
        initial_shape = df.shape

        llm = ChatGoogleGenerativeAI(
            model=config.FLASH_MODEL,
            google_api_key=config.GEMINI_API_KEY
        )
        logger.info("Requesting cleaning plan from LLM...")
        plan = ask_cleanup_plan(
            df=df,
            domain=state.get("data_domain", "unknown"),
            issues=state.get("issues_found", []),
            llm = llm
        )
        logger.info(f" {plan.get('reasoning', '')}")
        
        
        #change build
        df, actions = execute_plan(df, plan)
        final_shape = df.shape
        
        total_cells = df.shape[0] * df.shape[1]
        null_cells = int(df.isnull().sum().sum())
        new_quality = round(((total_cells - null_cells) / total_cells) * 100, 2
        ) if total_cells > 0 else 100.0
        
        cleaning_report ={
            "initial_shape" : list(initial_shape),
            "final_shape" : list(final_shape),
            "actions_taken" : actions,
            "new_quality_score":new_quality,
            "llm_reasoning": plan.get("reasoning", ""),
            "llm_plan": plan
        }
        
        return{
            **state,
            "cleaned_df" : df,
            "cleaning_report" : cleaning_report,
            "quality_score" : new_quality,
            "next_agent":"supervisor",
            "status" :"running"
        }
        
    except Exception as e :
        logger.error(f"Cleaner failed: {e}")
        logger.error(traceback.format_exc())
        return {**state, "error": str(e), "status" : "failed"}