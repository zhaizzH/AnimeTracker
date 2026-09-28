"""Compare public API signatures before and after the Lombok migration.

javap snapshots taken pre-migration live under ``target/sig-before``. This
script re-captures the current classes and reports any difference in the
public/protected surface, which is what R3 requires to stay identical. Private
members are ignored because delombok renames internal helpers such as
``$default$foo``.

Usage:
    python sig_compare.py <module> [<module> ...]
"""
from pathlib import Path
import os
import re
import subprocess
import sys

BUSINESS = Path("backend/business")
BEFORE = Path("target/sig-before")

# javap member lines begin with an optional modifier list then the return type.
VISIBLE = re.compile(r"^\s{2}(public|protected)\s")
CLASS_LINE = re.compile(r"^(public|protected|final|abstract|class|interface|enum).*\{")


def capture(classes_dir):
    """Return {fqcn: [visible member lines]} for every class under `classes_dir`."""
    files = [p for p in classes_dir.rglob("*.class") if "$" not in p.name]
    if not files:
        return {}
    fq = sorted(str(p.relative_to(classes_dir)).replace(os.sep, ".")[:-6] for p in files)
    result = subprocess.run(["javap", "-p", "-classpath", str(classes_dir), *fq],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    out, current = {}, None
    for line in result.stdout.splitlines():
        if line.endswith("{"):
            current = line.rstrip(" {").strip()
            if current.startswith("Compiled from"):
                continue
            out[current] = []
        elif current and VISIBLE.match(line):
            out[current].append(re.sub(r"\s+", " ", line.strip()))
    return out


def normalize(entry):
    """Strip the delombok-only helper names so private noise cannot mask real drift."""
    return re.sub(r"\$default\$|default(?=[A-Z])", "", entry)


def main():
    """Diff the visible surface of the named modules and report drift."""
    modules = sys.argv[1:] or ["common"]
    total_drift = 0
    for module in modules:
        classes = BUSINESS / module / "target" / "classes"
        before_file = BEFORE / f"{module}.txt"
        if not classes.exists() or not before_file.exists():
            print(f"[skip] {module}: missing classes or baseline snapshot")
            continue
        after = capture(classes)
        before = {}
        current = None
        for line in before_file.read_text(encoding="utf-8").splitlines():
            if line.endswith("{"):
                current = line.rstrip(" {").strip()
                before[current] = []
            elif current and VISIBLE.match(line):
                before[current].append(re.sub(r"\s+", " ", line.strip()))

        drift = []
        for cls in sorted(set(before) | set(after)):
            b = sorted(normalize(x) for x in before.get(cls, []))
            a = sorted(normalize(x) for x in after.get(cls, []))
            if b != a:
                only_before = [x for x in b if x not in a]
                only_after = [x for x in a if x not in b]
                drift.append((cls, only_before, only_after))
        if drift:
            total_drift += len(drift)
            print(f"[DRIFT] {module}: {len(drift)} class(es)")
            for cls, ob, oa in drift[:10]:
                print(f"    {cls}")
                for x in ob:
                    print(f"      - {x}")
                for x in oa:
                    print(f"      + {x}")
        else:
            print(f"[OK] {module}: {len(after)} classes, visible surface identical")
    return 1 if total_drift else 0


if __name__ == "__main__":
    sys.exit(main())
