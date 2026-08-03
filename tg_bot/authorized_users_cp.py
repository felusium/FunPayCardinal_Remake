"""
В данном модуле описаны функции для ПУ настроек авторизованных пользователей.
Модуль реализован в виде плагина.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import telebot.apihelper

if TYPE_CHECKING:
    from cardinal import Cardinal
from tg_bot import keyboards as kb, CBT, utils
from telebot.types import CallbackQuery
import logging

from locales.localizer import Localizer

logger = logging.getLogger("TGBot")
localizer = Localizer()
_ = localizer.translate


def init_authorized_users_cp(crd: Cardinal, *args):
    tg = crd.telegram
    bot = tg.bot

    def open_authorized_users_list(c: CallbackQuery):
        """
        Открывает список пользователей, авторизованных в ПУ.
        """
        offset = int(c.data.split(":")[1])
        bot.edit_message_text(_("desc_au"), c.message.chat.id, c.message.id,
                              reply_markup=kb.authorized_users(crd, offset))

    def open_authorized_user_settings(c: CallbackQuery):
        """
        Отркрывает настройки конкретного пользователя
        """
        __, user_id, offset = c.data.split(":")
        user_id = int(user_id)
        offset = int(offset)
        text = _("au_user_settings", f"<a href='tg:user?id={user_id}'>{user_id}</a>")
        try:
            bot.edit_message_text(text, c.message.chat.id,
                                  c.message.id,
                                  reply_markup=kb.authorized_user_settings(crd, user_id, offset, True))
        except telebot.apihelper.ApiTelegramException:
            logger.warning(_("crd_tg_au_err", user_id))
            logger.debug("TRACEBACK", exc_info=True)
            bot.edit_message_text(text, c.message.chat.id, c.message.id,
                                  reply_markup=kb.authorized_user_settings(crd, user_id, offset, False))

    def ask_delete_authorized_user(c: CallbackQuery):
        __, user_id, offset = c.data.split(":")
        user_id = int(user_id)
        offset = int(offset)
        text = _("au_delete_confirm", f"<a href='tg:user?id={user_id}'>{user_id}</a>")
        try:
            bot.edit_message_text(text, c.message.chat.id, c.message.id,
                                  reply_markup=kb.authorized_user_settings(crd, user_id, offset, True, True))
        except telebot.apihelper.ApiTelegramException:
            logger.warning(_("crd_tg_au_err", user_id))
            logger.debug("TRACEBACK", exc_info=True)
            bot.edit_message_text(text, c.message.chat.id, c.message.id,
                                  reply_markup=kb.authorized_user_settings(crd, user_id, offset, False, True))
        bot.answer_callback_query(c.id)

    def delete_authorized_user(c: CallbackQuery):
        __, user_id, offset = c.data.split(":")
        user_id = int(user_id)
        offset = int(offset)
        if user_id in tg.authorized_users and len(tg.authorized_users) <= 1 and crd.MAIN_CFG["Telegram"].getboolean("blockLogin"):
            bot.answer_callback_query(c.id, _("au_last_user_blocked"), show_alert=True)
            return

        tg.authorized_users.pop(user_id, None)
        utils.save_authorized_users(tg.authorized_users)

        scoped = tg.notification_settings.get(tg.notification_scope)
        if isinstance(scoped, dict):
            scoped.pop(f"user:{user_id}", None)
            utils.save_notification_settings(tg.notification_settings)

        bot.edit_message_text(_("au_user_deleted", user_id), c.message.chat.id, c.message.id,
                              reply_markup=kb.authorized_users(crd, offset))
        bot.answer_callback_query(c.id)

    def toggle_authorized_user_notifications(c: CallbackQuery):
        __, user_id, offset = c.data.split(":")
        user_id = int(user_id)
        offset = int(offset)
        enabled = tg.toggle_notification_recipient(user_id)
        text = _("au_user_settings", f"<a href='tg:user?id={user_id}'>{user_id}</a>")
        try:
            bot.edit_message_text(text, c.message.chat.id, c.message.id,
                                  reply_markup=kb.authorized_user_settings(crd, user_id, offset, True))
        except telebot.apihelper.ApiTelegramException:
            logger.warning(_("crd_tg_au_err", user_id))
            logger.debug("TRACEBACK", exc_info=True)
            bot.edit_message_text(text, c.message.chat.id, c.message.id,
                                  reply_markup=kb.authorized_user_settings(crd, user_id, offset, False))
        bot.answer_callback_query(
            c.id,
            "Уведомления будут приходить этому пользователю." if enabled else
            "Ограничение снято: уведомления снова идут по обычным настройкам."
        )

    tg.cbq_handler(open_authorized_users_list, lambda c: c.data.startswith(f"{CBT.AUTHORIZED_USERS}:"))
    tg.cbq_handler(open_authorized_user_settings, lambda c: c.data.startswith(f"{CBT.AUTHORIZED_USER_SETTINGS}:"))
    tg.cbq_handler(ask_delete_authorized_user, lambda c: c.data.startswith(f"{CBT.DELETE_AUTHORIZED_USER}:"))
    tg.cbq_handler(delete_authorized_user, lambda c: c.data.startswith(f"{CBT.CONFIRM_DELETE_AUTHORIZED_USER}:"))
    tg.cbq_handler(toggle_authorized_user_notifications,
                   lambda c: c.data.startswith(f"{CBT.TOGGLE_AUTHORIZED_USER_NOTIFICATIONS}:"))


BIND_TO_PRE_INIT = [init_authorized_users_cp]
