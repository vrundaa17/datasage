import sys 
from pathlib import Path 

PROJECT_ROOT = Path(__file__).resolve().parents[2] 
if str(PROJECT_ROOT) not in sys.path: 
    sys.path.insert(0, str(PROJECT_ROOT))
    
from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.supervisor import supervisor_node, route_next
from agents.inspector import inspect_node
from agents.cleaner import clean_node
from agents.eda import eda_node
from agents.reporter import reporter_node
from core.logger import get_logger

logger = get_logger(__name__)

def create_graph():
    graph = StateGraph(AgentState)
    
    #start-
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("inspect", inspect_node)
    graph.add_node("cleaner", clean_node) 
    graph.add_node("eda",eda_node)
    graph.add_node("reporter",reporter_node)
    
    graph.set_entry_point("supervisor")
    
    graph.add_conditional_edges(
        "supervisor", route_next, {
            "inspect": "inspect",
            "cleaner": "cleaner", 
            "eda": "eda",
            "reporter": "reporter",
            "end": END,
        }
    )
    graph.add_edge("inspect", "supervisor")
    graph.add_edge("cleaner","supervisor")
    graph.add_edge("eda","supervisor")
    graph.add_edge("reporter","supervisor")
    
    return graph.compile()