import logging
import sys


def setup_logging() -> logging.Logger:
    """Set up a structured logger."""
    logger = logging.getLogger("rag_api")
    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


logger = setup_logging()
