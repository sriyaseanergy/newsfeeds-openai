import logging


def build_default_formatter() -> logging.Formatter:
    """
    Build the shared log formatter used by console and file handlers.
    """
    return logging.Formatter(
        fmt=(
            "%(asctime)s %(levelname)s %(name)s "
            "%(funcName)s:%(lineno)d %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

