"""所有 Vector Set 能力检查共用的 ``COMMAND INFO`` 响应解析。

本模块是 ``command_info_present`` 的唯一定义。它不得引入内部依赖：
``vector_set`` 已经导入 ``subject_index``，若再复制一份（或反向导入），
要么重复判断逻辑，要么造成导入环。
"""

from __future__ import annotations

from typing import Any, Mapping


def command_info_present(info: Any) -> bool:
    """Redis 对未知的 COMMAND INFO 条目返回 ``[None]``。"""
    if not info:
        return False
    if isinstance(info, Mapping):
        return any(item is not None for item in info.values())
    if isinstance(info, (list, tuple)):
        return any(item is not None for item in info)
    return True
