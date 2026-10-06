"""预检 Bangumi 原始字段长度，找出会溢出 MySQL 列宽的值。

在跑全量导入前做一次，避免跑到一半才发现某个字段超长导致整条目事务回滚。
"""

import os
from collections import defaultdict

from dotenv import load_dotenv

load_dotenv(".env")

from jobs.importer.client import BangumiClient

# 列宽参照 docs/database/db-schema.sql
LIMITS = {
    "subject.name": 255, "subject.name_cn": 255, "subject.image": 512,
    "subject_tag.name": 32,
    "episode.name": 255, "episode.name_cn": 255, "episode.duration": 16,
    "person.name": 255, "person.image": 512,
    "character.name": 255, "character.image": 512,
    "subject_relation.relation": 32,
    "subject_character.relation": 32,
    "subject_person.relation": 32,
}

stats = defaultdict(lambda: {"max": 0, "sample": "", "over": 0, "seen": 0})


def note(field, value):
    if not isinstance(value, str):
        return
    s = stats[field]
    s["seen"] += 1
    if len(value) > s["max"]:
        s["max"], s["sample"] = len(value), value[:80]
    limit = LIMITS.get(field)
    if limit and len(value) > limit:
        s["over"] += 1


def main():
    c = BangumiClient(
        access_token=os.getenv("BANGUMI_ACCESS_TOKEN"),
        user_agent=os.getenv("BANGUMI_USER_AGENT") or "zhaizzH/AnimeTracker",
    )
    page = c.browse_subjects(type=2, offset=0, limit=60)
    ids = [e["id"] for e in (page.get("data") or [])]

    for sid in ids:
        try:
            d = c.get_subject(sid)
        except Exception as e:
            print("subject fail", sid, type(e).__name__)
            continue
        note("subject.name", d.get("name"))
        note("subject.name_cn", d.get("name_cn"))
        note("subject.image", (d.get("images") or {}).get("large"))
        for t in d.get("tags") or []:
            note("subject_tag.name", t.get("name"))

        for p in c.get_subject_persons(sid) or []:
            note("person.name", p.get("name"))
            note("person.image", (p.get("images") or {}).get("large"))
            note("subject_person.relation", p.get("relation"))
        for ch in c.get_subject_characters(sid) or []:
            note("character.name", ch.get("name"))
            note("character.image", (ch.get("images") or {}).get("large"))
            note("subject_character.relation", ch.get("relation"))
        for ep in c.get_all_episodes(sid) or []:
            note("episode.name", ep.get("name"))
            note("episode.name_cn", ep.get("name_cn"))
            note("episode.duration", ep.get("duration"))

    print(f"扫描 {len(ids)} 个条目\n")
    print(f"{'字段':<30}{'列宽':>6}{'最长':>6}{'超限':>6}  最长值")
    problems = []
    for field, s in sorted(stats.items()):
        limit = LIMITS.get(field)
        flag = ""
        if limit and s["over"]:
            flag = "  <== 超限"
            problems.append(field)
        print(f"{field:<30}{limit if limit else '-':>6}{s['max']:>6}{s['over']:>6}  {s['sample']!r}{flag}")

    print()
    if problems:
        print("需处理的字段:", ", ".join(problems))
    else:
        print("未发现超限字段")


if __name__ == "__main__":
    main()
