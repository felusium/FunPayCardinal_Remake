"""
Проверка на обновления.
"""
import time
from logging import getLogger
from locales.localizer import Localizer
import requests
import os
import zipfile
import shutil
import json

logger = getLogger("FPC.update_checker")
localizer = Localizer()
_ = localizer.translate

HEADERS = {
    "accept": "application/vnd.github+json"
}


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


def zipdir(path, zip_obj):
    """
    Рекурсивно архивирует папку.

    :param path: путь до папки.
    :param zip_obj: объект zip архива.
    """
    for root, dirs, files in os.walk(path):
        if os.path.basename(root) == "__pycache__":
            continue
        for file in files:
            zip_obj.write(os.path.join(root, file),
                          os.path.relpath(os.path.join(root, file),
                                          os.path.join(path, '..')))


def create_backup() -> int:
    """
    Создает резервную копию с папками storage и configs.

    :return: 0, если бэкап создан успешно, иначе - 1.
    """
    try:
        with zipfile.ZipFile("backup.zip", "w") as zip:
            zipdir("storage", zip)
            zipdir("configs", zip)
            zipdir("plugins", zip)
        return 0
    except:
        logger.debug("TRACEBACK", exc_info=True)
        return 1


def extract_backup_archive() -> bool:
    """
    Разархивирует скачанный backup.zip. в storage/cache/backup/

    :return: True, если разархивировано. False в случае ошибок.
    """
    try:
        if os.path.exists("storage/cache/backup/"):
            shutil.rmtree("storage/cache/backup/", ignore_errors=True)
        os.makedirs("storage/cache/backup")

        with zipfile.ZipFile("storage/cache/backup.zip", "r") as zip:
            zip.extractall("storage/cache/backup/")
        return True
    except:
        logger.debug("TRACEBACK", exc_info=True)
        return False


def install_release(folder_name: str) -> int:
    """
    Устанавливает обновление.

    :param folder_name: название папки со скачанным обновлением в storage/cache/update
    :return: 0, если обновление установлено.
        1 - произошла непредвиденная ошибка.
        2 - папка с обновлением отсутствует.
    """
    return 1


def install_backup() -> bool:
    """
    Устанавливает бэкап.
    """
    try:
        backup_folder = "storage/cache/backup"
        if not os.path.exists(backup_folder):
            return False

        for i in os.listdir(backup_folder):
            source = os.path.join(backup_folder, i)

            if os.path.isfile(source):
                shutil.copy2(source, i)
            else:
                shutil.copytree(source, os.path.join(".", i), dirs_exist_ok=True)
        return True
    except:
        logger.debug("TRACEBACK", exc_info=True)
        return False
