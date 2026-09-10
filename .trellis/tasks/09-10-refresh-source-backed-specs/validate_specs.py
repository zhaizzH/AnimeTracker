"""Check local Markdown links, rooted source references and spec indexes."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SPEC = ROOT / ".trellis/spec"
errors = []
links = 0
refs = set()
files = sorted(SPEC.rglob("*.md"))
for path in files:
    text = path.read_text(encoding="utf-8")
    for match in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", text):
        target = match.group(1).split("#", 1)[0]
        if not target or "://" in target:
            continue
        links += 1
        if not (path.parent / target).exists():
            errors.append(f"broken link: {path.relative_to(ROOT)} -> {target}")
    for match in re.finditer(r"`((?:backend/|frontend/|docs/|\.github/|\.trellis/)[^`\s]+)`", text):
        target = match.group(1).split("::", 1)[0]
        if any(mark in target for mark in ("*", "{", "}", "…", "...", "|")):
            continue
        if Path(target).suffix not in {".py", ".ts", ".tsx", ".mts", ".json", ".java", ".xml", ".sql", ".md", ".yaml", ".yml"}:
            continue
        refs.add(target)
        if not (ROOT / target).exists():
            errors.append(f"missing source: {path.relative_to(ROOT)} -> {target}")
    if re.search(r"To be filled|TODO: fill", text, re.I):
        errors.append(f"unfilled template: {path.relative_to(ROOT)}")
for directory in (SPEC / "backend", SPEC / "frontend", SPEC / "guides"):
    index = (directory / "index.md").read_text(encoding="utf-8")
    for doc in directory.glob("*.md"):
        if doc.name != "index.md" and f"./{doc.name}" not in index:
            errors.append(f"not indexed: {doc.relative_to(ROOT)}")
print(f"spec_files={len(files)} local_links={links} source_references={len(refs)} errors={len(errors)}")
for error in errors:
    print(error)
raise SystemExit(bool(errors))
