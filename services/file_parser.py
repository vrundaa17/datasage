from core.logger import get_logger
from core.config import config
from core.exce import UnsupportedFileTypeError, FileParsingError
from db.connection import SessionLocal
from db.models import User,Upload
import pandas as pd
import os, uuid

logger= get_logger(__name__)

def get_create_user(session_token):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.session_token == session_token).first()
        if not user:
            user = User(user_id = uuid.uuid4(), session_token =session_token)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user: {session_token[:5]}")
        return user 
    except Exception as e:
        db.rollback()
        logger.error(f"User error : {e}")
        raise
    finally:
        db.close()
        
        
def parse_file(file):
    try:
        filename = file.name
        ext = os.path.splitext(filename)[1].lower()
        if ext not in config.ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeError(f"File type {ext} not supported \nUse [{config.ALLOWED_EXTENSIONS}]")
        if ext =='.csv':
            df = pd.read_csv(file)
        elif ext in [".xlsx",".xls"]:
            df = pd.read_excel(file)
        
        if df.empty:
            raise FileParsingError("File is empty")
        logger.info(f"File parsed: {len(df)}rows | {len(df.columns)}cols")
        return df
        
    except UnsupportedFileTypeError:
        raise
    except FileParsingError:
        raise
    except Exception as e:
        logger.error(f"File parsing failed: {e}")
        raise FileParsingError(f"Could not parse your file {e}")
    
    
def save_upload(user_id, filename, filesize, df):
    db = SessionLocal()
    try:
        upload = Upload(
            upload_id = uuid.uuid4(),
            user_id= user_id, file_name = filename, file_size =filesize, status ="complete",
            row_count = len(df), column_count = len(df.columns)
        )
        db.add(upload)
        db.commit()
        db.refresh(upload)
        logger.info(f"Upload saved : {filename}")
        return upload
    except Exception as e:
        db.rollback()
        logger.error(f"Upload save failed : {e}")
        raise
    finally:
        db.close()
    
    
def handle_upload(file,session_token: str):
    df = parse_file(file)
    user = get_create_user(session_token)
    upload= save_upload(
        user_id = user.user_id,
        filename = file.name,
        filesize = file.size,
        df = df
    )
    return {"df":df, "user": user, "upload": upload}

