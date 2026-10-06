import os

class Settings:
    PROJECT_NAME: str = "AgentPrep - Visual Prep Compliance Agent"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./database.db")
    
    # AI Vision Provider Configuration
    VISION_PROVIDER: str = os.getenv("VISION_PROVIDER", "local")  # local, openai, gemini, etc.
    VISION_API_KEY: str = os.getenv("VISION_API_KEY", "")
    VISION_MODEL: str = os.getenv("VISION_MODEL", "gpt-4o-mini")
    OCR_PROVIDER: str = os.getenv("OCR_PROVIDER", "local")
    REASONING_PROVIDER: str = os.getenv("REASONING_PROVIDER", "rules")
    
    # Upload settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "static/uploads")
    SAMPLE_DIR: str = os.getenv("SAMPLE_DIR", "sample_data")
    MAX_UPLOAD_SIZE_MB: int = 10

settings = Settings()
