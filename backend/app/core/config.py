import os

class Settings:
    PROJECT_NAME: str = "E-Commerce Decision Intelligence Platform API"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"

    DB_HOST: str = os.getenv("DB_HOST", "postgres")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_USER: str = os.getenv("DB_USER", "dwh_user")
    DB_PASS: str = os.getenv("DB_PASS", "12345")
    DB_NAME: str = os.getenv("DB_NAME", "ecommerce_dwh")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*"
    ]

settings = Settings()
