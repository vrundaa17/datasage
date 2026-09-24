from db.connection import SessionLocal
from tools.db_writer import save_analysis_run, save_report, save_visualisations
from tools.chart_generator import generate_all_charts
from core.logger import get_logger

logger = get_logger(__name__)


def write_full_report(state: dict) -> dict:
    db = SessionLocal()
    try:
        # df = state.get("cleaned_df") or state.get("raw_df")
        # df = state.get("cleaned_df") if state.get("cleaned_df") is not None else state.get("raw_df")
        cleaned = state.get("cleaned_df")
        df = cleaned if cleaned is not None else state.get("raw_df")
        
        logger.info("[ REPORT WRITER ] Generating charts...")
        charts = generate_all_charts(df, state.get("visualisations", []))
        
        logger.info("[ REPORT WRITER ] Saving analysis run...")
        run_id = save_analysis_run(db, state)
        
        logger.info("[ REPORT WRITER ] Saving report...")
        report_id = save_report(db, state, run_id)
        
        logger.info("[ REPORT WRITER ] Saving visualisations...")
        vis_ids = save_visualisations(db, state, run_id, charts)

        logger.info(f"[ REPORT WRITER ] All saved. run_id={run_id}")

        return {
            "run_id":run_id,
            "report_id": report_id,
            "vis_ids": vis_ids,
            "charts": charts,
        }
        
        
    except Exception as e:
        logger.error(f"[ REPORT WRITER ] Failed: {e}")
        raise

    finally:
        db.close()