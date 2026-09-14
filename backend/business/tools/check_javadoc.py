"""Check Java declarations and JDK doclint after mvn -B clean test."""
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def main():
    """Return nonzero for missing contracts, malformed docs or unresolved links."""
    output = ROOT / "target" / "javadoc-check"
    output.mkdir(parents=True, exist_ok=True)
    coverage = subprocess.run(
        ["java", "-Dfile.encoding=UTF-8", str(ROOT / "tools/CheckJavadoc.java"), str(ROOT)],
        encoding="utf-8", errors="replace", capture_output=True)
    (output / "coverage.txt").write_text(coverage.stdout + coverage.stderr, encoding="utf-8")
    print(coverage.stdout, end="")
    reports = sorted((ROOT / "app/target/surefire-reports").glob("TEST-*.xml"))
    if not reports:
        print("Run mvn -B clean test in backend/business first.", file=sys.stderr)
        return 1
    properties = ET.parse(reports[0]).getroot().find("properties")
    classpath = next((p.attrib["value"] for p in properties
                      if p.attrib["name"] == "java.class.path"), None)
    if not classpath:
        print("Surefire report has no resolved classpath.", file=sys.stderr)
        return 1
    sources = sorted(p for p in ROOT.rglob("*.java") if "target" not in p.relative_to(ROOT).parts)
    args = ["-private", "-quiet", "-encoding", "UTF-8", "-docencoding", "UTF-8",
            "-Xdoclint:all,-missing", "-Werror", "-classpath", classpath,
            "-d", str(output / "html")] + [str(p) for p in sources]
    argfile = output / "javadoc.args"
    argfile.write_text("\n".join('"' + a.replace(chr(92), "/").replace('"', chr(92) + '"') + '"'
                                 for a in args), encoding="utf-8")
    lint = subprocess.run(["javadoc", "-J-Dfile.encoding=UTF-8", "@" + str(argfile)],
                          encoding="utf-8", errors="replace", capture_output=True)
    (output / "doclint.txt").write_text(lint.stdout + lint.stderr, encoding="utf-8")
    if lint.returncode:
        print(lint.stderr, file=sys.stderr)
    print(f"Declaration check: {coverage.returncode}; doclint: {lint.returncode}; reports: {output}")
    return int(bool(coverage.returncode or lint.returncode))


if __name__ == "__main__":
    sys.exit(main())
