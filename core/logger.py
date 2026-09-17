import logging 
import os
from core.config import config

def get_logger(name: str)-> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(config.LOG_LEVEL)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger