import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = "sqlite:///./src/database/properties_management.db"
    
    # Google Gemini
    google_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash"
    
    # Agent
    agent_enabled: bool = True
    
    # Email Configuration
    smtp_host: str = os.getenv("SMTP_HOST")
    smtp_port: int = os.getenv("SMTP_PORT")
    smtp_user: Optional[str] = os.getenv("SMTP_USER")
    smtp_password: Optional[str] = os.getenv("SMTP_PASSWORD")
    smtp_from_email: Optional[str] = os.getenv("SMTP_FROM_EMAIL")
    email_enabled: bool = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    
    # Company settings
    company_name: str = "Properties Management"
    company_phone: Optional[str] = None
    company_address: Optional[str] = None
    support_email: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
