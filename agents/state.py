from typing import TypedDict, Optional, Any

class AgentState(TypedDict):
    # data
    raw_df : Optional[Any]              #original
    cleaned_df : Optional[Any]          #after clean
    
    # Inspect
    column_names : list
    data_types : dict
    null_counts : dict
    row_count : int
    column_count : int
    sample_values :dict
    quality_score : float           #100-0
    issues_found : list
    data_domain : str
    
    # clean
    cleaning_report : dict
    
    # analysis
    analysis_results : dict
    key_findings : list
    visualisations : list
    
    # result
    report : str
    
    # qa
    conversation_history : list
    current_question : str
    question_type : str
    followup_answer : str
    
    # supervisor
    next_agent : str
    instructions : str
    iteration_count : int
    
    # meta
    user_id : str
    upload_id : str
    error : Optional[str]
    status : str                    #running/failed/completed