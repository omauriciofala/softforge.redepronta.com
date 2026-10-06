import logging
import sys

from loguru import logger

from src.config import settings


class InterceptHandler(logging.Handler):
    """Intercepta logs da biblioteca padrão do Python e redireciona para o Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    """Configura o sistema de logging do projeto."""
    # Remove handlers padrão
    logger.remove()

    if settings.LOG_FORMAT == "json":
        # Formato JSON para produção (fácil de analisar por agentes e ferramentas)
        logger.add(
            sys.stdout,
            level=settings.LOG_LEVEL,
            serialize=True,
            enqueue=True,
            backtrace=True,
            diagnose=False,
        )
    else:
        # Formato colorido para desenvolvimento local
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        logger.add(
            sys.stdout,
            level=settings.LOG_LEVEL,
            format=log_format,
            colorize=True,
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )

    # Redireciona logs de uvicorn e fastapi
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for uvicorn_logger in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"):
        logging.getLogger(uvicorn_logger).handlers = [InterceptHandler()]
        logging.getLogger(uvicorn_logger).propagate = False


__all__ = ["logger", "setup_logging"]
