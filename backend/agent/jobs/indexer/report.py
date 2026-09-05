from __future__ import annotations

from dataclasses import asdict, dataclass
import ctypes
import json
import os
from pathlib import Path


@dataclass(frozen=True)
class CapacityReport:
    sample_count: int
    bytes_per_document: int
    projected_total_bytes: int
    redis_used_memory: int
    physical_available: int
    utilization: float
    allowed: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def build_capacity_report(
    *,
    sample_bytes: int,
    sample_count: int,
    catalog_count: int,
    redis_used_memory: int,
    available_bytes: int,
) -> CapacityReport:
    if sample_bytes < 0 or sample_count < 0 or catalog_count < 0 or redis_used_memory < 0 or available_bytes < 1:
        raise ValueError("容量报告参数无效")
    if sample_count == 0:
        return CapacityReport(0, 0, 0, redis_used_memory, available_bytes, 0.0, False)
    # 向上取整，避免样本大小不能整除时低估全量索引占用。
    bytes_per_document = (sample_bytes + sample_count - 1) // sample_count
    projected_total_bytes = bytes_per_document * catalog_count
    utilization = projected_total_bytes / available_bytes
    return CapacityReport(
        sample_count,
        bytes_per_document,
        projected_total_bytes,
        redis_used_memory,
        available_bytes,
        utilization,
        utilization <= 0.6,
    )


def physical_available_memory() -> int:
    if os.name == "nt":
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        status = MEMORYSTATUSEX()
        status.dwLength = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.ullAvailPhys)
    try:
        return int(os.sysconf("SC_AVPHYS_PAGES")) * int(os.sysconf("SC_PAGE_SIZE"))
    except (AttributeError, ValueError, OSError):
        raise RuntimeError("无法读取物理可用内存") from None


def write_report(path: str | Path, report: CapacityReport, **metrics: object) -> None:
    payload = report.as_dict() | metrics
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
