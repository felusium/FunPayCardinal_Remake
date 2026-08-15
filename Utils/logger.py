"""
В данном модуле написаны форматтеры для логгера.
"""
from colorama import Fore, Back, Style
import logging.handlers
import logging
import atexit
import queue
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
        record.args = None
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
        record.args = None
        formatter = logging.Formatter(FILE_LOG_FORMAT, FILE_TIME_FORMAT)
        return redact_sensitive(formatter.format(record))


LOGGER_NAMES = ["main", "FunPayAPI", "FPC", "TGBot"]


class _QueueHandler(logging.handlers.QueueHandler):
    def prepare(self, record: logging.LogRecord) -> logging.LogRecord:
        return record


def configure_logging() -> logging.handlers.QueueListener:
    cli_handler = logging.StreamHandler()
    cli_handler.setLevel(logging.INFO)
    cli_handler.setFormatter(CLILoggerFormatter())
    cli_handler.addFilter(lambda record: record.name != "TeleBot")

    file_handler = logging.handlers.RotatingFileHandler(
        filename="logs/log.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=25,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(FileLoggerFormatter())

    log_queue = queue.SimpleQueue()
    queue_handler = _QueueHandler(log_queue)

    for name in LOGGER_NAMES:
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(queue_handler)

    telebot_logger = logging.getLogger("TeleBot")
    telebot_logger.setLevel(logging.ERROR)
    telebot_logger.propagate = False
    telebot_logger.addHandler(queue_handler)

    listener = logging.handlers.QueueListener(log_queue, cli_handler, file_handler, respect_handler_level=True)
    listener.start()
    atexit.register(listener.stop)
    return listener
