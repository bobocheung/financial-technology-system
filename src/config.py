from pathlib import Path


# 全域路徑設定（可依需求調整）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def ensure_directories() -> None:
    """確保主要輸出資料夾存在。"""
    for directory in [DATA_DIR, MODELS_DIR, OUTPUTS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
