from __future__ import annotations

from datetime import datetime
from pathlib import Path


def cleanup_old_logs(log_dir: Path, keep_days: int = 2) -> list[Path]:
    """
    Delete log files older than the newest `keep_days` daily files.

    Expected file name format: YYYY-MM-DD.log
    """
    log_dir.mkdir(parents=True, exist_ok=True)

    dated_files: list[tuple[datetime, Path]] = []
    for file_path in log_dir.glob("*.log"):
        try:
            parsed_date = datetime.strptime(file_path.stem, "%Y-%m-%d")
        except ValueError:
            # Ignore non-date log files in this directory.
            continue
        dated_files.append((parsed_date, file_path))

    dated_files.sort(key=lambda item: item[0], reverse=True)
    files_to_delete = [path for _, path in dated_files[keep_days:]]

    for file_path in files_to_delete:
        file_path.unlink(missing_ok=True)

    return files_to_delete

