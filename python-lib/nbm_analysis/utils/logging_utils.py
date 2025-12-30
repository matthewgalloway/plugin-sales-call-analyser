import logging, os
import importlib.util


class AppLogger:

    def __init__(self, log_level: str, name=None):

        self._log_level = log_level
        self._name = name

        level = getattr(logging, log_level.upper())
        if not isinstance(level, int):
            raise ValueError(f"Invalid log level: {log_level}")

        if self._name is None:
            self._logger = logging.getLogger(__name__)
        else:
            self._logger = logging.getLogger(self._name)

        self._logger.setLevel(level)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        self._logger.propagate = False

    def debug(self, msg: str, *args, **kwargs) -> None:
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        self._logger.info(msg, *args, **kwargs)

    def warn(self, msg: str, *args, **kwargs) -> None:
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self._logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        self._logger.critical(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs) -> None:
        self._logger.exception(msg, *args, **kwargs)


def get_logger(module_name: str) -> AppLogger:

    log_level = os.getenv("FLASK_LOG_LEVEL")
    if not log_level:
        raise Exception("app configuration lacks a specified 'FLASK_LOG_LEVEL")
    logger = AppLogger(log_level, module_name + ".py")
    return logger
