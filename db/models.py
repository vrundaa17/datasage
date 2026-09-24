from sqlalchemy import Column, String, Integer , Float,Text,DateTime,JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from db.connection import Base, engine
from core.logger import get_logger
import uuid
logger= get_logger(__name__)

class User(Base):
    __tablename__= "users"
    
    user_id= Column(UUID(as_uuid=True),primary_key=True, default=uuid.uuid4)
    creatd_at= Column(DateTime, server_default = func.now())
    session_token= Column(String,unique=True)
    last_active = Column(DateTime, onupdate = func.now())

class Upload(Base):
    __tablename__="uploads"
    
    upload_id= Column(UUID(as_uuid=True),primary_key=True, default =uuid.uuid4)
    user_id	= Column(UUID(as_uuid=True),ForeignKey("users.user_id"))
    file_name= Column(String)	
    file_size= Column(Integer)
    uploaded_at= Column(DateTime, server_default = func.now())
    status= Column(String , default="processing")
    row_count= Column(Integer)
    column_count= Column(Integer)

class AnalysisRun(Base):
    __tablename__="analysis_runs"
    
    run_id=Column(UUID(as_uuid=True),primary_key=True, default =uuid.uuid4)
    user_id= Column(UUID(as_uuid=True),ForeignKey("users.user_id"))
    upload_id= Column(UUID(as_uuid=True),ForeignKey("uploads.upload_id"))
    started_at= Column(DateTime, server_default = func.now())
    completed_at=Column(DateTime)
    status=Column(String, default="running")
    data_domain=Column(String)
    quality_score=Column(Float)
####
    cleaning_report=Column(JSON)
    analysis_result=Column(JSON)
    key_finding=Column(JSON)
    
    row_count=Column(Integer)

class Report(Base):
    __tablename__="reports"
    
    report_id= Column(UUID(as_uuid=True),primary_key=True, default =uuid.uuid4)
    user_id= Column(UUID(as_uuid=True),ForeignKey("users.user_id"))
    run_id= Column(UUID(as_uuid=True),ForeignKey("analysis_runs.run_id"))
    created_at=Column(DateTime, server_default = func.now())
    report_text	=Column(Text)
    summary = Column(Text)
    recommendation=Column(JSON)


class Visualisations(Base):
    __tablename__="visualisations"
    
    vis_id = Column(UUID(as_uuid=True),primary_key=True, default =uuid.uuid4)
    user_id= Column(UUID(as_uuid=True),ForeignKey("users.user_id"))
    run_id= Column(UUID(as_uuid=True),ForeignKey("analysis_runs.run_id"))
    chart_type= Column(String)
    title = Column(String)
    plotly_json = Column(JSON)
    created_at=Column(DateTime, server_default = func.now())
    
class Conversation(Base):
    __tablename__ ="conversations"
    
    conversation_id=Column(UUID(as_uuid=True),primary_key=True, default =uuid.uuid4)
    user_id= Column(UUID(as_uuid=True),ForeignKey("users.user_id"))
    run_id=Column(UUID(as_uuid=True),ForeignKey("analysis_runs.run_id"))
    started_at=Column(DateTime, server_default = func.now())
    
class Message(Base):
    __tablename__="messages"
    
    message_id=Column(UUID(as_uuid=True),primary_key=True, default =uuid.uuid4)
    conversation_id	=Column(UUID(as_uuid=True),ForeignKey("conversations.conversation_id"))
    user_id= Column(UUID(as_uuid=True),ForeignKey("users.user_id"))
    role=Column(String)
    content=Column(Text)
    question_type=Column(String)
    raw_data= Column(JSON)
    created_at=Column(DateTime, server_default = func.now())
    


def create_tables():
    logger.info("Creating Database tables")
    # Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully")
    
if __name__ == "__main__":
    create_tables()