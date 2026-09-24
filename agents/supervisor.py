import sys 
from pathlib import Path 

PROJECT_ROOT = Path(__file__).resolve().parents[1] 
if str(PROJECT_ROOT) not in sys.path: 
    sys.path.insert(0, str(PROJECT_ROOT))
    
from agents.state import AgentState
from core.logger import get_logger


logger = get_logger(__name__)


MAX_ITERATIONS = 10

def supervisor_node(state: AgentState) -> AgentState:
    logger.info("[ SUPERVISOR ] evaluating state")
    
   

    iteration = state.get("iteration_count", 0)
    if iteration >= MAX_ITERATIONS:
        logger.warning("Max iterations reached, forcing end")
        return {**state, "next_agent": "end"}
    
    inspect_done= bool(state.get('data_domain'))
    cleaner_done = bool(state.get('cleaning_report'))
    eda_done = bool(state.get('analysis_results'))
    report_done = bool(state.get('report'))
    has_error = bool(state.get('error'))
    has_question= bool(state.get("current_question"))
    # answer_done = bool(state.get("followup_answer"))
    
    if has_error:
        next_agent = 'end'
    elif not inspect_done:
        next_agent = "inspect"
    elif not cleaner_done:
        next_agent = "cleaner"
    elif not eda_done:
        next_agent = 'eda'
    elif not report_done:
        next_agent = "reporter"
    elif has_question:
        next_agent = "reporter"      
    else:
        next_agent = 'end'
    
    logger.info(f'[ SUPERVISOR ] : {next_agent}')
    
    return {
        **state,
        "next_agent" : next_agent,
        "iteration_count" : iteration + 1
    }
    
    

def route_next(state: AgentState) -> str:
    return state.get("next_agent", "end")