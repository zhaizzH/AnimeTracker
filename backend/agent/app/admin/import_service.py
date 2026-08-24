from app.admin.ports import JobLauncher


class ImportAlreadyRunning(Exception):
    """已有导入子进程存活，触发被拒绝。"""


class ImportService:
    def __init__(self, launcher: JobLauncher):
        self._launcher = launcher

    def run(
        self,
        mode: str,
        *,
        key: str | None = None,
        since: str | None = None,
        workers: int | None = None,
    ) -> None:
        if mode not in {"full", "season", "recent", "since"}:
            raise ValueError("mode 必须是 full / season / recent / since")
        if mode == "season" and not key:
            raise ValueError("season 模式需要 key")
        if mode == "since" and not since:
            raise ValueError("since 模式需要 since")
        self._launcher.start_import(mode, key=key, since=since, workers=workers)
