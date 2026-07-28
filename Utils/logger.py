"""
В данном модуле написаны форматтеры для логгера.
"""
from colorama import Fore, Back, Style
import logging.handlers
import logging
import re


LOG_COLORS = {
        logging.DEBUG: Fore.BLACK + Style.BRIGHT,
        logging.INFO: Fore.GREEN,
        logging.WARN: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Back.RED
}

CLI_LOG_FORMAT = f"{Fore.BLACK + Style.BRIGHT}[%(asctime)s]{Style.RESET_ALL}"\
                 f"{Fore.CYAN}>{Style.RESET_ALL} $RESET%(levelname).1s: %(message)s{Style.RESET_ALL}"
CLI_TIME_FORMAT = "%d-%m-%Y %H:%M:%S"

FILE_LOG_FORMAT = "[%(asctime)s][%(filename)s][%(lineno)d]> %(levelname).1s: %(message)s"
FILE_TIME_FORMAT = "%d.%m.%y %H:%M:%S"
CLEAR_RE = re.compile(r"(\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]))|(\n)|(\r)")
SENSITIVE_REPLACEMENTS = (
    (re.compile(r"/bot\d+:[A-Za-z0-9_-]+"), "/bot<hidden>"),
    (re.compile(r"\b\d{6,15}:[A-Za-z0-9_-]{25,}\b"), "<telegram_token>"),
    (re.compile(r"(jwt=)[^&\s]+", re.IGNORECASE), r"\1<hidden>"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"), "<jwt>"),
    (re.compile(r"([?&](?:token|auth|key|signature|sig|golden_key)=)[^&\s]+", re.IGNORECASE), r"\1<hidden>"),
    (
        re.compile(
            r"((?:[\"']?(?:golden_key|goldenKey|token|password|passwd|secret)[\"']?\s*[:=]\s*[\"']?))"
            r"[^\"'\s,;}]+([\"']?)",
            re.IGNORECASE
        ),
        r"\1<hidden>\2"
    ),
    (re.compile(r"(Authorization:\s*Bearer\s+)[^\s,;]+", re.IGNORECASE), r"\1<hidden>"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "<email>"),
)


def redact_sensitive(text: str) -> str:
    text = str(text)
    for pattern, replacement in SENSITIVE_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    return text


def add_colors(text: str) -> str:
    """
    Заменяет ключевые слова на коды цветов.

    $YELLOW - желтый текст.

    $CYAN - светло-голубой текст.

    $MAGENTA - фиолетовый текст.

    $BLUE - синий текст.

    :param text: текст.

    :return: цветной текст.
    """
    colors = {
        "$YELLOW": Fore.YELLOW,
        "$CYAN": Fore.CYAN,
        "$MAGENTA": Fore.MAGENTA,
        "$BLUE": Fore.BLUE,
        "$GREEN": Fore.GREEN,
        "$BLACK": Fore.BLACK,
        "$WHITE": Fore.WHITE,

        "$B_YELLOW": Back.YELLOW,
        "$B_CYAN": Back.CYAN,
        "$B_MAGENTA": Back.MAGENTA,
        "$B_BLUE": Back.BLUE,
        "$B_GREEN": Back.GREEN,
        "$B_BLACK": Back.BLACK,
        "$B_WHITE": Back.WHITE,
    }
    for c in colors:
        if c in text:
            text = text.replace(c, colors[c])
    return text


class CLILoggerFormatter(logging.Formatter):
    """
    Форматтер для вывода логов в консоль.
    """
    def __init__(self):
        super(CLILoggerFormatter, self).__init__()

    def format(self, record: logging.LogRecord) -> str:
        msg = redact_sensitive(record.getMessage())
        msg = add_colors(msg)
        msg = msg.replace("$RESET", LOG_COLORS[record.levelno])
        record.msg = msg
        log_format = CLI_LOG_FORMAT.replace("$RESET", Style.RESET_ALL + LOG_COLORS[record.levelno])
        formatter = logging.Formatter(log_format, CLI_TIME_FORMAT)
        return redact_sensitive(formatter.format(record))


class FileLoggerFormatter(logging.Formatter):
    """
    Форматтер для сохранения логов в файл.
    """
    def __init__(self):
        super(FileLoggerFormatter, self).__init__()

    def format(self, record: logging.LogRecord) -> str:
        msg = redact_sensitive(record.getMessage())
        msg = CLEAR_RE.sub("", msg)
        record.msg = msg
        formatter = logging.Formatter(FILE_LOG_FORMAT, FILE_TIME_FORMAT)
        return redact_sensitive(formatter.format(record))


LOGGER_CONFIG = {
    "version": 1,
    "handlers": {
        "file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "file_formatter",
            "filename": "logs/log.log",
            "maxBytes": 5 * 1024 * 1024,  # 5 MB
            "backupCount": 25,
            "encoding": "utf-8"
        },

        "cli_handler": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "cli_formatter"
        }
    },

    "formatters": {
        "file_formatter": {
            "()": "Utils.logger.FileLoggerFormatter"
        },

        "cli_formatter": {
            "()": "Utils.logger.CLILoggerFormatter"
        }
    },

    "loggers": {
        "main": {
            "handlers": ["cli_handler", "file_handler"],
            "level": "DEBUG"
        },
        "FunPayAPI": {
            "handlers": ["cli_handler", "file_handler"],
            "level": "DEBUG"
        },
        "FPC": {
            "handlers": ["cli_handler", "file_handler"],
            "level": "DEBUG"
        },
        "TGBot": {
            "handlers": ["cli_handler", "file_handler"],
            "level": "DEBUG"
        },
        "TeleBot": {
            "handlers": ["file_handler"],
            "level": "ERROR",
            "propagate": "False"
        }
    }
}
