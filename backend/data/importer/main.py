"""
AnimeTracker 数据导入器入口

从 Bangumi API 导入动漫数据到 MySQL 数据库。
支持四种模式: --full / --recent / --season / --since

用法:
    python main.py --full
    python main.py --recent
    python main.py --season 2024-spring
    python main.py --since 2024-01-01
"""

from import_runner import run_import


def main():
    run_import()


if __name__ == "__main__":
    main()
