import logging
import sys

from settings.settings import settings


class SafeConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        msg = self.format(record)
        stream = self.stream
        encoded = msg.encode(stream.encoding, errors="replace").decode(
            stream.encoding
        )
        stream.write(encoded + self.terminator)
        self.flush()


def setup_shared_logger(name, log_file="kodo.log"):
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )

    console_handler = SafeConsoleHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        logger.addHandler(console_handler)

        if getattr(settings, "log_to_file", True):
            file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)
            logger.addHandler(file_handler)

    return logger


logger = setup_shared_logger("kodo")
