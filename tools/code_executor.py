import pandas as pd
import traceback,time
from core.logger import get_logger
from core.exce import CodeExecutionError

logger = get_logger(__name__)

MAX_RETRIES = 3 

def _llm_with_retry(llm, prompt: str) -> str:
    """Call LLM with retry on rate limit."""
    for attempt in range(3):
        try:
            response = llm.invoke(prompt)
            content = response.content
            if isinstance(content, list):
                content = "".join(
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in content
                )
        
            raw = content.strip()
            return raw
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 15 * (attempt + 1)
                logger.warning(f"Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                if attempt == 2:
                    raise
            else:
                raise
            

def execute_code(code, df: pd.DataFrame):
    local_vars ={ "df": df.copy(),"pd": pd,"result": None }
    try:
        exec(code, {}, local_vars)
        return{"success" : True,  "result" : local_vars.get("result"),
            "df" : local_vars.get("df"),  "error" : None
        }
    except Exception as e:
        error_msg = traceback.format_exc()
        logger.error(f"Code execution failed : {error_msg}")
        return { "success" : False, "result" : None, "df" : df,"error" : str(e) }


def execute_with_retry(code_fn , df: pd.DataFrame, context):
    last_error=None
    for attempt in range(MAX_RETRIES):
        code = code_fn(last_error)
        logger.info(f"Attempt {attempt}: executing")
        result = execute_code(code,df)
        
        if result['success']:
            logger.info("Code execution successful")
            return result

        last_error = result['error']
        logger.warning(f"Attempt {attempt}: failed")
    logger.error(f"All {MAX_RETRIES}  attempt failed")
    raise CodeExecutionError(f"Code execution failed after {MAX_RETRIES} attempts. \nLast Error : {last_error}")

