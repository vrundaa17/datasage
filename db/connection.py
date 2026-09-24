from core.config import config
from core.logger import get_logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,DeclarativeBase

logger = get_logger(__name__)

class Base(DeclarativeBase):
    pass

engine  = create_engine(config.DATABASE_URL, echo= config.APP_ENV =="development")

SessionLocal = sessionmaker(autocommit=False, autoflush = False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e :
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        
