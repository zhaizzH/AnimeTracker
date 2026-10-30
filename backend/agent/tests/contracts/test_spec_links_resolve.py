"""`.trellis/spec/**` 里的 markdown 链接目标必须可解析。

由来（2026-10-30）：归档任务目录后，`agent-ui-actions.md` 里三条指向
`../../tasks/10-29-*/design.md` 的链接全部断掉——文档看着正常，点进去 404。
同一轮还发现 spec 的 Tests Required 指向 `tests/chat/test_runs_replay.py`（目录根本不存在）。

## 为什么只查链接，不查正文里的裸路径

试过按正则抽正文里的 `xxx.py` / `xxx.tsx` 断言存在，结果误报淹没了信号：
`*.test.ts(x)` 是命名模式、`spring.sql` 是配置键、`authority_enrich.py` 是
spec 里明说「曾写成这个名字、实际叫 authority.py」的历史说明。
区分「路径」与「命名模式/配置键/历史名」需要读语义，机械检查做不到。

markdown 链接 `](target)` 是**无语义歧义的**：它一定指向一个文件或目录。
所以这里只查那一类。更严的正文路径检查需要人工，已写进
`agent-ui-actions.md` 的复核要求与 retro 记录，不在这里硬做。

放在 `tests/contracts/` 是刻意的：CI 里这一组单独成步（`contract drift`），
失败标题直接说明是文档漂移，而不是混在全量用例里的一条匿名 FAILED。
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_SPEC_ROOT = Path(__file__).resolve().parents[4] / ".trellis" / "spec"

# 只认 markdown 行内链接；排除外链、页内锚点、邮件
_LINK_RE = re.compile(r"\]\((?!https?:|mailto:|#)(?P<target>[^)\s]+)\)")


def _iter_spec_files() -> list[Path]:
    return sorted(_SPEC_ROOT.rglob("*.md"))


def _broken_links() -> list[str]:
    broken: list[str] = []
    for spec in _iter_spec_files():
        for match in _LINK_RE.finditer(spec.read_text(encoding="utf-8")):
            # 去掉 `#锚点` 与行尾标点，只留路径部分
            target = match.group("target").split("#", 1)[0].rstrip(".,;)")
            if not target:
                continue
            if not (spec.parent / target).exists():
                where = spec.relative_to(_SPEC_ROOT.parents[1]).as_posix()
                broken.append(f"{where} -> {target}")
    return broken


def test_spec_markdown_links_resolve() -> None:
    spec_files = _iter_spec_files()
    assert spec_files, f"没有找到任何 spec 文件：{_SPEC_ROOT}"

    broken = _broken_links()
    assert not broken, (
        "spec 里的 markdown 链接指向不存在的路径"
        "（任务归档后最常断在这里，记得同步改成 archive/ 下的路径）：\n  "
        + "\n  ".join(broken)
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
