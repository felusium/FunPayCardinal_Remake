"""
В данном модуле реализован загрузчик файлов из телеграм чата.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from cardinal import Cardinal
    from tg_bot.bot import TGBot

from Utils import config_loader as cfg_loader, exceptions as excs, cardinal_tools, updater
from telebot.types import InlineKeyboardButton as Button
from tg_bot import utils, keyboards, CBT
from tg_bot.static_keyboards import CLEAR_STATE_BTN
from telebot import types
import logging
import os

logger = logging.getLogger("TGBot")  # locale#locale#locale


def check_file(tg: TGBot, msg: types.Message, type_: Literal["py", "cfg", "json", "txt"] | None = None) -> bool:
    """
    Проверяет выгруженный файл. Отправляет сообщение в TG в зависимости от ошибки.

    :param tg: экземпляр TG бота.

    :param msg: экземпляр сообщения.

    :param type_: формат файла.

    :return: True, если все ок, False, если файл проверку не прошел.
    """
    if not msg.document:
        tg.bot.send_message(msg.chat.id, "❌ Файл не знайдено.")
        return False
    if not any((msg.document.file_name.endswith(".cfg"), msg.document.file_name.endswith(".txt"),
                msg.document.file_name.endswith(".py"), msg.document.file_name.endswith(".json"))):
        tg.bot.send_message(msg.chat.id, "❌ Файл має бути текстовим.")
        return False
    if type_ is not None and not msg.document.file_name.endswith(f".{type_}"):
        tg.bot.send_message(msg.chat.id, f"❌ Неправильний формат файлу: "
                                         f"<b><u>.{msg.document.file_name.split('.')[-1]}</u></b> "
                                         f"(замість <b><u>.{type_}</u></b>)")
        return False
    if msg.document.file_size >= 20971520:
        tg.bot.send_message(msg.chat.id, "❌ Розмір файлу не має перевищувати 20МБ.")
        return False
    return True


def download_file(tg: TGBot, msg: types.Message, file_name: str = "temp_file.txt",
                  custom_path: str = "") -> bool:
    """
    Скачивает выгруженный файл и сохраняет его в папку storage/cache/.

    :param tg: экземпляр TG бота.

    :param msg: экземпляр сообщения.

    :param file_name: название сохраненного файла.

    :param custom_path: кастомный путь (если надо сохранить не в storage/cache/).

    :return: True, если все ок, False, при ошибке.
    """
    tg.bot.send_message(msg.chat.id, "⏬ Завантажую файл...")
    try:
        file_info = tg.bot.get_file(msg.document.file_id)
        file = tg.bot.download_file(file_info.file_path)
    except:
        tg.bot.send_message(msg.chat.id, "❌ Сталася помилка при завантаженні файлу.")
        logger.debug("TRACEBACK", exc_info=True)
        return False

    path = f"storage/cache/{file_name}" if not custom_path else os.path.join(custom_path, file_name)
    with open(path, "wb") as new_file:
        new_file.write(file)
    return True


def init_uploader(cardinal: Cardinal):
    tg = cardinal.telegram
    bot = tg.bot

    def act_upload_products_file(c: types.CallbackQuery):
        result = bot.send_message(c.message.chat.id, "Відправ мені файл із товарами.",
                                  reply_markup=CLEAR_STATE_BTN())
        tg.set_state(c.message.chat.id, result.id, c.from_user.id, CBT.UPLOAD_PRODUCTS_FILE)
        bot.answer_callback_query(c.id)

    def upload_products_file(m: types.Message):
        """
        Загружает файл с товарами.
        """
        tg.clear_state(m.chat.id, m.from_user.id, True)
        if not check_file(tg, m, type_="txt"):
            return
        if not download_file(tg, m, m.document.file_name,
                             custom_path=f"storage/products"):
            return

        try:
            products_count = cardinal_tools.count_products(f"storage/products/{utils.escape(m.document.file_name)}")
        except:
            bot.send_message(m.chat.id, "❌ Сталася помилка при підрахунку товарів.")
            logger.debug("TRACEBACK", exc_info=True)
            return

        file_number = os.listdir("storage/products").index(m.document.file_name)

        keyboard = types.InlineKeyboardMarkup() \
            .add(Button("✏️ Редагувати файл", callback_data=f"{CBT.EDIT_PRODUCTS_FILE}:{file_number}:0"))

        logger.info(f"Користувач $MAGENTA@{m.from_user.username} (id: {m.from_user.id})$RESET "
                    f"завантажив у бота файл із товарами $YELLOWstorage/products/{m.document.file_name}$RESET.")

        bot.send_message(m.chat.id,
                         f"✅ Файл із товарами <code>storage/products/{m.document.file_name}</code> успішно завантажено. "
                         f"Товарів у файлі: <code>{products_count}.</code>",
                         reply_markup=keyboard)

    def act_upload_main_config(c: types.CallbackQuery):
        result = bot.send_message(c.message.chat.id, "Відправ мені основний конфіг.",
                                  reply_markup=CLEAR_STATE_BTN())
        tg.set_state(c.message.chat.id, result.id, c.from_user.id, "upload_main_config")
        bot.answer_callback_query(c.id)

    def upload_main_config(m: types.Message):
        """
        Загружает и проверяет основной конфиг.
        """
        tg.clear_state(m.chat.id, m.from_user.id, True)
        if not check_file(tg, m, type_="cfg"):
            return
        if not download_file(tg, m, "temp_main.cfg"):
            return

        bot.send_message(m.chat.id, "🔁 Перевіряю валідність файлу...")
        try:
            new_config = cfg_loader.load_main_config("storage/cache/temp_main.cfg")
        except excs.ConfigParseError as e:
            bot.send_message(m.chat.id, f"❌ Сталася помилка при обробці основного конфіга: "
                                        f"<code>{utils.escape(str(e))}</code>")
            return
        except UnicodeDecodeError:
            bot.send_message(m.chat.id,
                             "Сталася помилка при розшифруванні <code>UTF-8</code>. Переконайся, що кодування "
                             "файлу = <code>UTF-8</code>, а формат кінця рядків = <code>LF</code>.")
            return
        except:
            bot.send_message(m.chat.id, "❌ Сталася помилка при перевірці конфіга автовидачі.")
            logger.debug("TRACEBACK", exc_info=True)
            return

        cardinal.save_config(new_config, "configs/_main.cfg")
        logger.info(f"Користувач $MAGENTA@{m.from_user.username} (id: {m.from_user.id})$RESET "
                    f"завантажив у бота основний конфіг.")
        bot.send_message(m.chat.id, "✅ Основний конфіг успішно завантажено. \n"
                                    "Потрібно перезапустити бота, щоб застосувати зміни. \n"
                                    "Будь-яка зміна основного конфіга через перемикачі в панелі скасує всі зміни.")

    def act_upload_auto_response_config(c: types.CallbackQuery):
        result = bot.send_message(c.message.chat.id, "Відправ мені конфіг автовідповідача.",
                                  reply_markup=CLEAR_STATE_BTN())
        tg.set_state(c.message.chat.id, result.id, c.from_user.id, "upload_auto_response_config")
        bot.answer_callback_query(c.id)

    def upload_auto_response_config(m: types.Message):
        """
        Загружает, проверяет и устанавливает конфиг автовыдачи.
        """
        tg.clear_state(m.chat.id, m.from_user.id, True)
        if not check_file(tg, m, type_="cfg"):
            return
        if not download_file(tg, m, "temp_auto_response.cfg"):
            return

        bot.send_message(m.chat.id, "🔁 Перевіряю валідність файлу...")
        try:
            new_config = cfg_loader.load_auto_response_config("storage/cache/temp_auto_response.cfg")
            raw_new_config = cfg_loader.load_raw_auto_response_config("storage/cache/temp_auto_response.cfg")
        except excs.ConfigParseError as e:
            bot.send_message(m.chat.id, f"❌ Сталася помилка при обробці конфіга автовідповідача: "
                                        f"<code>{utils.escape(str(e))}</code>")
            return
        except UnicodeDecodeError:
            bot.send_message(m.chat.id,
                             "Сталася помилка при розшифруванні <code>UTF-8</code>. Переконайся, що кодування "
                             "файлу = <code>UTF-8</code>, а формат кінця рядків = <code>LF</code>.")
            return
        except:
            bot.send_message(m.chat.id, "❌ Сталася помилка при перевірці конфіга автовідповідача.")
            logger.debug("TRACEBACK", exc_info=True)
            return

        cardinal.RAW_AR_CFG, cardinal.AR_CFG = raw_new_config, new_config
        cardinal.save_config(cardinal.RAW_AR_CFG, "configs/auto_response.cfg")

        logger.info(f"Користувач $MAGENTA@{m.from_user.username} (id: {m.from_user.id})$RESET "
                    f"завантажив у бота та встановив конфіг автовідповідача.")
        bot.send_message(m.chat.id, "✅ Конфіг автовідповідача успішно застосовано.")

    def act_upload_auto_delivery_config(c: types.CallbackQuery):
        result = bot.send_message(c.message.chat.id, "Відправ мені конфіг автовидачі.",
                                  reply_markup=CLEAR_STATE_BTN())
        tg.set_state(c.message.chat.id, result.id, c.from_user.id, "upload_auto_delivery_config")
        bot.answer_callback_query(c.id)

    def upload_auto_delivery_config(m: types.Message):
        """
        Загружает, проверяет и устанавливает конфиг автовыдачи.
        """
        tg.clear_state(m.chat.id, m.from_user.id, True)
        if not check_file(tg, m, type_="cfg"):
            return
        if not download_file(tg, m, "temp_auto_delivery.cfg"):
            return

        bot.send_message(m.chat.id, "🔁 Перевіряю валідність файлу...")
        try:
            new_config = cfg_loader.load_auto_delivery_config("storage/cache/temp_auto_delivery.cfg")
        except excs.ConfigParseError as e:
            bot.send_message(m.chat.id, f"❌ Сталася помилка при обробці конфіга автовидачі: "
                                        f"<code>{utils.escape(str(e))}</code>")
            return
        except UnicodeDecodeError:
            bot.send_message(m.chat.id,
                             "Сталася помилка при розшифруванні <code>UTF-8</code>. Переконайся, що кодування "
                             "файлу = <code>UTF-8</code>, а формат кінця рядків = <code>LF</code>.")
            return
        except:
            bot.send_message(m.chat.id, "❌ Сталася помилка при перевірці конфіга автовидачі.")
            logger.debug("TRACEBACK", exc_info=True)
            return

        cardinal.AD_CFG = new_config
        cardinal.save_config(cardinal.AD_CFG, "configs/auto_delivery.cfg")

        logger.info(f"Користувач $MAGENTA@{m.from_user.username} (id: {m.from_user.id})$RESET "
                    f"завантажив у бота та встановив конфіг автовидачі.")
        bot.send_message(m.chat.id, "✅ Конфіг автовидачі успішно застосовано.")

    def upload_plugin(m: types.Message):
        offset = tg.get_state(m.chat.id, m.from_user.id)["data"]["offset"]
        tg.clear_state(m.chat.id, m.from_user.id, True)
        if not check_file(tg, m, type_="py"):
            return
        if not download_file(tg, m, f"{utils.escape(m.document.file_name)}", custom_path="plugins"):
            return

        logger.info(f"[IMPORTANT] Користувач $MAGENTA@{m.from_user.username} (id: {m.from_user.id})$RESET "
                    f"завантажив у бота плагін $YELLOWplugins/{m.document.file_name}$RESET.")

        keyboard = types.InlineKeyboardMarkup() \
            .add(Button("Назад", callback_data=f"{CBT.PLUGINS_LIST}:{offset}"))
        bot.send_message(m.chat.id,
                         f"✅ Плагін <code>{utils.escape(m.document.file_name)}</code> успішно завантажено.\n\n"
                         f"Щоб плагін активувався, перезапусти бота командою /restart.",
                         reply_markup=keyboard)

    def send_funpay_image(m: types.Message):
        data = tg.get_state(m.chat.id, m.from_user.id)["data"]
        chat_id, username = data["node_id"], data["username"]
        tg.clear_state(m.chat.id, m.from_user.id, True)
        if not m.photo:
            tg.bot.send_message(m.chat.id, "❌ Підтримуються тільки формати <code>.png</code>, <code>.jpg</code>, "
                                           "<code>.gif</code>.")
            return
        photo = m.photo[-1]
        if photo.file_size >= 20971520:
            tg.bot.send_message(m.chat.id, "❌ Розмір файлу не має перевищувати 20МБ.")
            return

        try:
            file_info = tg.bot.get_file(photo.file_id)
            file = tg.bot.download_file(file_info.file_path)
            image_id = cardinal.account.upload_image(file, type_="chat")
            result = cardinal.send_message(chat_id, f"$photo={image_id}", username)
            if not result:
                raise Exception("Немає повідомлень")
            tg.bot.reply_to(m, f'✅ Повідомлення відправлено в переписку '
                               f'<a href="https://funpay.com/chat/?node={chat_id}">{username}</a>.',
                            reply_markup=keyboards.reply(chat_id, username, again=True))
        except:
            logger.warning("Сталася помилка при відправленні зображення.")
            logger.debug("TRACEBACK", exc_info=True)
            tg.bot.reply_to(m, f'❌ Не вдалося відправити повідомлення в переписку '
                               f'<a href="https://funpay.com/chat/?node={chat_id}">{username}</a>. '
                               f'Детальніше у файлі <code>logs/log.log</code>',
                            reply_markup=keyboards.reply(chat_id, username, again=True))
            return

    def upload_image(m: types.Message, type_: Literal["chat", "offer"] = "chat"):
        tg.clear_state(m.chat.id, m.from_user.id, True)
        if not m.photo:
            tg.bot.send_message(m.chat.id, "❌ Підтримуються тільки формати <code>.png</code>, <code>.jpg</code>, "
                                           "<code>.gif</code>.")
            return
        photo = m.photo[-1]
        if photo.file_size >= 20971520:
            tg.bot.send_message(m.chat.id, "❌ Розмір файлу не має перевищувати 20МБ.")
            return

        try:
            file_info = tg.bot.get_file(photo.file_id)
            file = tg.bot.download_file(file_info.file_path)
            image_id = cardinal.account.upload_image(file, type_=type_)
        except:
            tg.bot.reply_to(m, f'❌ Не вдалося завантажити зображення. '
                               f'Детальніше у файлі <code>logs/log.log</code>')
            return
        if type_ == "chat":
            s = f"Використовуй цей ID у текстах автовидачі/автовідповіді зі змінною " \
                f"<code>$photo</code>\n\n" \
                f"Наприклад: <code>$photo={image_id}</code>"
        elif type_ == "offer":
            s = f"Використовуй цей ID для додавання зображень до лотів."
        bot.reply_to(m, f"✅ Зображення завантажено на сервер FunPay.\n\n"
                        f"<b>ID:</b> <code>{image_id}</code>\n\n{s}")

    def upload_chat_image(m: types.Message):
        upload_image(m, type_="chat")

    def upload_offer_image(m: types.Message):
        upload_image(m, type_="offer")

    tg.cbq_handler(act_upload_products_file, lambda c: c.data == CBT.UPLOAD_PRODUCTS_FILE)
    tg.cbq_handler(act_upload_auto_response_config, lambda c: c.data == "upload_auto_response_config")
    tg.cbq_handler(act_upload_auto_delivery_config, lambda c: c.data == "upload_auto_delivery_config")
    tg.cbq_handler(act_upload_main_config, lambda c: c.data == "upload_main_config")

    tg.file_handler(CBT.UPLOAD_PRODUCTS_FILE, upload_products_file)
    tg.file_handler("upload_auto_response_config", upload_auto_response_config)
    tg.file_handler("upload_auto_delivery_config", upload_auto_delivery_config)
    tg.file_handler("upload_main_config", upload_main_config)
    tg.file_handler(CBT.UPLOAD_PLUGIN, upload_plugin)
    tg.file_handler(CBT.SEND_FP_MESSAGE, send_funpay_image)
    tg.file_handler(CBT.UPLOAD_CHAT_IMAGE, upload_chat_image)
    tg.file_handler(CBT.UPLOAD_OFFER_IMAGE, upload_offer_image)


BIND_TO_PRE_INIT = [init_uploader]
