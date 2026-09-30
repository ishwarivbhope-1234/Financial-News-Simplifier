import os
from pathlib import Path

# Load .env file manually or with dotenv if available
def load_environment():
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).resolve().parent.parent / ".env"
        load_dotenv(dotenv_path=env_path)
    except ImportError:
        # Fallback manual parser if python-dotenv is not installed
        env_path = Path(__file__).resolve().parent.parent / ".env"
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        if key and key not in os.environ:
                            os.environ[key] = val

load_environment()

class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "").strip()
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    @property
    def has_groq_key(self) -> bool:
        return bool(self.GROQ_API_KEY and not self.GROQ_API_KEY.startswith("your_"))

    @property
    def has_news_api_key(self) -> bool:
        return bool(self.NEWS_API_KEY and not self.NEWS_API_KEY.startswith("your_"))

settings = Settings()
