import logging


def configure_logging(level: str) -> None:
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    root_logger.setLevel(level)
