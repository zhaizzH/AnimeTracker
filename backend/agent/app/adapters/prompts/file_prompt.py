import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_RESOURCES_DIR = Path(__file__).resolve().parents[3] / "resources"
_PROMPT_DIR = _RESOURCES_DIR / "prompt"
_PROMPT_CACHE: dict[str, str] = {}


def load_prompt(name: str) -> str:
    if name in _PROMPT_CACHE:
        return _PROMPT_CACHE[name]
    path = _PROMPT_DIR / name
    if not path.is_file():
        logger.warning("提示词文件不存在: %s", path)
        return ""
    text = path.read_text(encoding="utf-8")
    _PROMPT_CACHE[name] = text
    return text
