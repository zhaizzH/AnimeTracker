import re
from datetime import datetime

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


def sanitize_import_error(error: Exception | str) -> str:
    """保留可诊断的异常类型，同时移除连接串、凭据与令牌。"""
    message = str(error).replace("\r", " ").replace("\n", " ")
    message = re.sub(r"(?i)\bauthorization\s*:\s*bearer\s+[^\s,;]+", "Authorization: Bearer ***", message)
    message = re.sub(r"(?i)\b(?:authorization|password|passwd|pwd|token|api[_-]?key)\s*[:=]\s*[^\s,;]+", "***", message)
    message = re.sub(r"(?i)\bbearer\s+[^\s,;]+", "Bearer ***", message)
    message = re.sub(r"//[^:/@\s]+:[^@/\s]+@", "//***:***@", message)
    message = re.sub(r"\beyJ[A-Za-z0-9._-]+", "***", message)
    message = re.sub(r"(?i)\b(?:password|passwd|pwd|token|api[_-]?key|authorization)\b", "***", message)
    return f"{type(error).__name__}: {message[:240]}"


def get_engine(host: str, port: int, user: str, password: str, db: str):
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600)


def fail_stale_running_records(session: Session, message: str = "导入进程提前退出") -> None:
    """把未正常结束的 RUNNING 导入记录翻为 FAILED（进程硬退兜底）。"""
    session.execute(
        text("""
            UPDATE import_record
            SET status = 'FAILED', completed_at = :now, error_message = :message
            WHERE status = 'RUNNING'
              AND (heartbeat_at IS NULL OR heartbeat_at < DATE_SUB(:now, INTERVAL 10 MINUTE))
        """),
        {"now": datetime.now(), "message": sanitize_import_error(message)},
    )
