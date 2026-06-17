from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CHANGENOW_API_KEY: str = "286b57bcb3f2745052a36ef5165c26680267977009ea099acd2c5915a6b5e54c"
    CHANGENOW_API_SECRET: str = "286b57bcb3f2745052a36ef5165c26680267977009ea099acd2c5915a6b5e54c"
    CHANGENOW_BASE_URL: str = "https://api.changenow.io/v2"
    COMMISSION_PERCENT: float = 1.5
    DATABASE_URL: str = "sqlite:///./cris.db"
    BASE_URL: str = "http://localhost:8000"
    FCM_SERVER_KEY: str = ""
    RATE_LIMIT_PER_MINUTE: int = 60
    AUTH_API_KEY: str = "cris-mobile-key-change-me-in-production"

    class Config:
        env_file = ".env"

settings = Settings()