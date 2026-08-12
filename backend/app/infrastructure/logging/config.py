from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from threading import RLock

from app.infrastructure.logging.cleanup import cleanup_old_logs
from app.infrastructure.logging.formatter import build_default_formatter

_LOGGER_CONFIG_FLAG = "_newsfeeds_logging_configured"
_DEFAULT_LOG_DIR = Path("logs")


class DailyLogFileHandler(logging.Handler):
    """
    File handler that writes to logs/YYYY-MM-DD.log and rotates at date boundary.

    This is an equivalent daily rotation mechanism tailored to required file names.
    """

    def __init__(self, log_dir: Path):
        super().__init__()
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._lock = RLock()
        self._active_date: str | None = None
        self._file_handler: logging.FileHandler | None = None
        self._ensure_handler_for_today()

    def _current_date_key(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def _ensure_handler_for_today(self) -> None:
        with self._lock:
            date_key = self._current_date_key()
            if self._file_handler is not None and self._active_date == date_key:
                return

            if self._file_handler is not None:
                self._file_handler.close()

            file_path = self.log_dir / f"{date_key}.log"
            self._file_handler = logging.FileHandler(
                filename=file_path,
                mode="a",
                encoding="utf-8",
            )
            self._active_date = date_key

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._ensure_handler_for_today()
            if self._file_handler is None:
                return
            msg = self.format(record)
            self._file_handler.stream.write(msg + "\n")
            self._file_handler.flush()
        except Exception:
            self.handleError(record)

    def close(self) -> None:
        with self._lock:
            if self._file_handler is not None:
                self._file_handler.close()
                self._file_handler = None
        super().close()


def configure_logging(
    level: int = logging.INFO,
    log_dir: Path = _DEFAULT_LOG_DIR,
    retention_days: int = 2,
) -> None:
    """
    Configure root logging with console + daily rotating file handlers once.
    """
    root_logger = logging.getLogger()
    if getattr(root_logger, _LOGGER_CONFIG_FLAG, False):
        return

    cleanup_old_logs(log_dir=log_dir, keep_days=retention_days)

    formatter = build_default_formatter()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = DailyLogFileHandler(log_dir=log_dir)
    file_handler.setFormatter(formatter)

    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    setattr(root_logger, _LOGGER_CONFIG_FLAG, True)


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured module logger.
    """
    configure_logging()
    return logging.getLogger(name)

