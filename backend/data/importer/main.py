"""
AnimeTracker 数据导入器入口

从 Bangumi API 导入动漫数据到 MySQL 数据库。
支持四种模式: --full / --recent / --season / --since
"""

from import_runner import run_import


def main():
    """CLI 入口"""
    run_import()


if __name__ == "__main__":
    main()
