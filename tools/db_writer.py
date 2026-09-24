import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from db.models import AnalysisRun, Report, Visualisations, Conversation, Message
from core.logger import get_logger

logger = get_logger(__name__)


def save_analysis_run(db: Session, state: dict) :
    try:
        run_id = uuid.uuid4()
        run=AnalysisRun(
            run_id= run_id,
            user_id= uuid.UUID(state["user_id"]) if isinstance(state["user_id"], str) else state["user_id"],
            upload_id = uuid.UUID(state["upload_id"]) if isinstance(state["upload_id"], str) else state["upload_id"],
            completed_at=datetime.now(timezone.utc),
            status="completed",
            data_domain=state.get("data_domain", ""),
            quality_score=state.get("quality_score", 0.0),
            cleaning_report=state.get("cleaning_report", {}),
            analysis_result=state.get("analysis_results", {}),
            key_finding=state.get("key_findings", []),
            row_count=state.get("row_count", 0),
        )
        
        db.add(run)
        db.commit()
        db.refresh(run)

        logger.info(f"[ DB ] AnalysisRun saved: {run_id}")
        return str(run_id)
    except Exception as e:
        db.rollback()
        logger.error(f"[ DB ] save_analysis_run failed: {e}")
        raise



def save_report(db: Session, state : dict, run_id : str):
    try:
        report_id = uuid.uuid4()
        report = Report(
            report_id= report_id,
            user_id = uuid.UUID(state["user_id"]) if isinstance(state["user_id"], str) else state["user_id"],
            run_id = uuid.UUID(run_id),
            report_text = state.get("report", ""),
            summary = None,
            recommendation = None
        )
        
        db.add(report)
        db.commit()
        db.refresh(report)

        logger.info(f"[ DB ] Report saved: {report_id}")
        return str(report_id)
    except Exception as e:
        db.rollback()
        logger.error(f"[ DB ] save_report failed: {e}")
        raise

def save_visualisations(db: Session, state : dict, run_id : str, charts):
    vis_ids = []
    try:
        for chart in charts:
            vis_id = uuid.uuid4()
            vis = Visualisations(
                vis_id= vis_id,
                user_id = uuid.UUID(state["user_id"]) if isinstance(state["user_id"], str) else state["user_id"],
                run_id = uuid.UUID(run_id),
                chart_type = chart.get("chart_type", ""),
                title = chart.get("title", ""),
                plotly_json = chart.get("plotly_json", {}),
            )
            db.add(vis)
            vis_ids.append(str(vis_id))

        db.commit()
        logger.info(f"[ DB ] {len(charts)} visualisations saved for run: {run_id}")
        return vis_ids
            
    except Exception as e:
        db.rollback()
        logger.error(f"[ DB ] save_visualisation falied :{e}")
        raise
    
def save_conversation_message(db:Session, user_id:str ,conversation_id:str , role:str, content:str, question_type):
    try:
        message_id = uuid.uuid4()

        msg = Message(
            message_id = message_id,
            conversation_id = uuid.UUID(conversation_id),
            user_id = uuid.UUID(user_id) if isinstance(user_id, str) else user_id,
            role  = role,
            content = content,
            question_type= question_type,
        )
        db.add(msg)
        db.commit()

        logger.info(f"[ DB ] Message saved: {role} | {message_id}")
        return str(message_id)
    except Exception as e:
        db.rollback()
        logger.error(f"[ DB ] save_conversation_message failed: {e}")
        raise

def create_conversation(db:Session,user_id : str,run_id : str):
    try:
        conv_id = uuid.uuid4()
        
        conv = Conversation(
            conversation_id = conv_id,
            user_id = uuid.UUID(user_id) if isinstance(user_id, str) else user_id,
            run_id = uuid.UUID(run_id),
        )

        db.add(conv)
        db.commit()

        logger.info(f"[ DB ] Conversation created: {conv_id}")
        return str(conv_id)
    except Exception as e:
        db.rollback()
        logger.error(f"[ DB ] create_conversation failed: {e}")
        raise