from __future__ import annotations
import logging
from logging import Logger


def configure_default_logging(logger: Logger, filepath: str):
    """
    Default configuration that can be used across all files
    """

    # Create handlers
    console_handler = logging.StreamHandler()  # Console handler
    file_handler = logging.FileHandler(filepath)  # File handler

    # Set level of logging
    logger.setLevel(logging.DEBUG)  # Could be ERROR, WARNING, INFO, DEBUG
    console_handler.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.DEBUG)

    # Create formatters and add it to handlers
    console_format = logging.Formatter("%(asctime)-24s %(name)-16s %(module)-16s %(levelname)-8s %(message)-32s")
    file_format = logging.Formatter("%(asctime)s -*- %(name)s -*- %(module)s:%(lineno)d -*- %(levelname)s -*- %(message)s")
    console_handler.setFormatter(console_format)
    file_handler.setFormatter(file_format)

    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
