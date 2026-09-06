import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    FAULT_INJECTION_ENABLED = os.getenv("FAULT_INJECTION_ENABLED", "false").lower() == "true"
    FAULT_PROBABILITY = os.getenv("FAULT_PROBABILITY", "0.10")
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
