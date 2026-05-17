"""
Проверка на обновления.
"""
from logging import getLogger
from locales.localizer import Localizer

logger = getLogger("FPC.update_checker")
localizer = Localizer()
_ = localizer.translate

class Release:
    """
    Класс, описывающий релиз.
    """

    def __init__(self, name: str, description: str, sources_link: str):
        """
        :param name: название релиза.
        :param description: описание релиза (список изменений).
        :param sources_link: ссылка на архив с исходниками.
        """
        self.name = name
        self.description = description
        self.sources_link = sources_link


# Получение данных о новом релизе
def get_tags(current_tag: str) -> list[str] | None:
    """
    Получает все теги с GitHub репозитория.
    :param current_tag: текущий тег.

    :return: список тегов.
    """
    return None


def get_next_tag(tags: list[str], current_tag: str):
    """
    Ищет след. тег после переданного.
    Если не находит текущий тег, возвращает первый.
    Если текущий тег - последний, возвращает None.

    :param tags: список тегов.
    :param current_tag: текущий тег.

    :return: след. тег / первый тег / None
    """
    try:
        curr_index = tags.index(current_tag)
    except ValueError:
        return tags[len(tags) - 1]

    if not curr_index:
        return None
    return tags[curr_index - 1]


def get_releases(from_tag: str) -> list[Release] | None:
    """
    Получает данные о доступных релизах, начиная с тега.

    :param from_tag: тег релиза, с которого начинать поиск.

    :return: данные релизов.
    """
    return None


def get_new_releases(current_tag) -> int | list[Release]:
    """
    Проверяет на наличие обновлений.

    :param current_tag: тег текущей версии.

    :return: список объектов релизов или код ошибки:
        1 - произошла ошибка при получении списка тегов.
        2 - текущий тег является последним.
        3 - не удалось получить данные о релизе.
    """
    return 2


#  Загрузка нового релиза
def download_zip(url: str) -> int:
    """
    Загружает zip архив с обновлением в файл storage/cache/update.zip.

    :param url: ссылка на zip архив.

    :return: 0, если архив с обновлением загружен, иначе - 1.
    """
    return 1


def extract_update_archive() -> str | int:
    """
    Разархивирует скачанный update.zip.

    :return: название папки с обновлением (storage/cache/update/<папка с обновлением>) или 1, если произошла ошибка.
    """
    return 1


def install_release(folder_name: str) -> int:
    """
    Устанавливает обновление.

    :param folder_name: название папки со скачанным обновлением в storage/cache/update
    :return: 0, если обновление установлено.
        1 - произошла непредвиденная ошибка.
        2 - папка с обновлением отсутствует.
    """
    return 1
