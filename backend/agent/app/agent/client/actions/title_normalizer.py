"""安全标题归一化：NFKC + 大小写折叠 + 标点分隔 + 空白折叠。

对查询和候选标题使用同一函数；不包含任何语义转换（如「第二季」→「第2季」）。
纯函数，无副作用。
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

# 归一化时被当作分隔符的安全标点（NFKC 之后全角多已折叠为半角）。
# 只处理字符层面，绝不映射任何语义变体。
_PUNCTUATION_RE = re.compile(
    r"[·・、,，.。!！?？~～\-—–‐_＿:：;；'\"’‘“”()（）\[\]【】{}｛｝<>《》|/\\+*=&^%$#@`]+"
)
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_title(value: Any) -> str:
    """安全标题归一化：NFKC + 大小写折叠 + 标点分隔 + 空白折叠 + 首尾清理。

    对查询和候选标题使用同一函数；不包含任何语义转换。
    """
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    text = _PUNCTUATION_RE.sub(" ", text)
    return _WHITESPACE_RE.sub(" ", text).strip()
