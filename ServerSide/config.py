"""
Configuration settings for the PDF Document Intelligence API
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file (only if file exists)
env_file = Path(".env")
if env_file.exists():
    load_dotenv()
    print("📄 Loaded .env file")
else:
    print("⚠️ No .env file found, using environment variables")

class Settings:
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "50000000"))  # 50MB
    ALLOWED_EXTENSIONS: list = [".pdf"]
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    TEMP_DIR: str = os.getenv("TEMP_DIR", "temp")
    
    # Processing Configuration
    MAX_CONCURRENT_JOBS: int = int(os.getenv("MAX_CONCURRENT_JOBS", "5"))
    JOB_TIMEOUT: int = int(os.getenv("JOB_TIMEOUT", "300"))  # 5 minutes
    CLEANUP_TEMP_FILES: bool = os.getenv("CLEANUP_TEMP_FILES", "true").lower() == "true"
    
    # Model Configuration
    MODEL_CACHE_DIR: str = os.getenv("MODEL_CACHE_DIR", "models")
    USE_LIGHTWEIGHT_MODELS: bool = os.getenv("USE_LIGHTWEIGHT_MODELS", "false").lower() == "true"
    
    # Google Gemini AI Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ENABLE_GEMINI_ANALYSIS: bool = os.getenv("ENABLE_GEMINI_ANALYSIS", "true").lower() == "true"
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    GEMINI_TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE", "0.1"))
    
    # Authentication Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    TOKEN_EXPIRE_HOURS: int = int(os.getenv("TOKEN_EXPIRE_HOURS", "24"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "api.log")
    
    def __init__(self):
        # Create necessary directories
        Path(self.UPLOAD_DIR).mkdir(exist_ok=True)
        Path(self.TEMP_DIR).mkdir(exist_ok=True)
        Path(self.MODEL_CACHE_DIR).mkdir(exist_ok=True)

# Global settings instance
settings = Settings()
