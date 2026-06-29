from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
UPLOADS_DIR = PROJECT_ROOT / "uploads"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
DB_PATH = DATA_DIR / "applications.db"

try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    # python-dotenv 是可选依赖；未安装时仍允许应用使用系统环境变量运行。
    pass


def ensure_directories() -> None:
    """确保项目运行需要的本地目录存在。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def get_llm_settings() -> dict:
    """读取 OpenAI-compatible API 配置；没有 Key 时返回空 Key，应用继续使用规则分析。"""
    return {
        "api_key": os.getenv("LLM_API_KEY", os.getenv("API_KEY", "")).strip(),
        "base_url": os.getenv("LLM_BASE_URL", os.getenv("BASE_URL", "https://api.openai.com/v1")).strip(),
        "model_name": os.getenv("LLM_MODEL_NAME", os.getenv("MODEL_NAME", "gpt-4o-mini")).strip(),
    }
