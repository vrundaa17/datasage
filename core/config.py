from dotenv import load_dotenv
import os 
load_dotenv()

class Config:
    # LLM
    GEMINI_API_KEY =  os.getenv("GEMINI_API_KEY")
    # GROQ_API_KEY=
    
    # database
    DATABASE_URL= os.getenv("DATABASE_URL")
    
    # app
    APP_ENV= os.getenv("APP_ENV",'development')
    LOG_LEVEL = os.getenv("LOG_LEVEL",'INFO')
    
    # model
    # FLASH_MODEL = 'gemini-1.5-flash'
    # PRO_MODEL =''
    
    # file
    MAX_FILE_SIZE =50
    ALLOWED_EXTENSIONS =[ '.csv','.xlsx', '.xls']
    
config = Config()