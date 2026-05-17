"""
Р’ РґР°РЅРЅРѕРј РјРѕРґСѓР»Рµ РЅР°РїРёСЃР°РЅС‹ С„СѓРЅРєС†РёРё РґР»СЏ РІР°Р»РёРґР°С†РёРё РєРѕРЅС„РёРіРѕРІ.
"""
import configparser
from configparser import ConfigParser, SectionProxy
import codecs
import os

from Utils.exceptions import (ParamNotFoundError, EmptyValueError, ValueNotValidError, SectionNotFoundError,
                              ConfigParseError, ProductsFileNotFoundError, NoProductVarError,
                              SubCommandAlreadyExists, DuplicateSectionErrorWrapper)
from Utils.cardinal_tools import hash_password, build_proxy


def check_param(param_name: str, section: SectionProxy, valid_values: list[str | None] | None = None,
                raise_if_not_exists: bool = True) -> str | None:
    """
    РџСЂРѕРІРµСЂСЏРµС‚, СЃСѓС‰РµСЃС‚РІСѓРµС‚ Р»Рё РІ РїРµСЂРµРґР°РЅРЅРѕР№ СЃРµРєС†РёРё СѓРєР°Р·Р°РЅРЅС‹Р№ РїР°СЂР°РјРµС‚СЂ Рё РµСЃР»Рё РґР°, РІР°Р»РёРґРЅРѕ Р»Рё РµРіРѕ Р·РЅР°С‡РµРЅРёРµ.

    :param param_name: РЅР°Р·РІР°РЅРёРµ РїР°СЂР°РјРµС‚СЂР°.
    :param section: РѕР±СЉРµРєС‚ СЃРµРєС†РёРё.
    :param valid_values: РІР°Р»РёРґРЅС‹Рµ Р·РЅР°С‡РµРЅРёСЏ. Р•СЃР»Рё None, Р»СЋР±Р°СЏ СЃС‚СЂРѕРєР° - РІР°Р»РёРґРЅРѕРµ Р·РЅР°С‡РµРЅРёРµ.
    :param raise_if_not_exists: РІРѕР·Р±СѓР¶РґР°С‚СЊ Р»Рё РёСЃРєР»СЋС‡РµРЅРёРµ, РµСЃР»Рё РїР°СЂР°РјРµС‚СЂ РЅРµ РЅР°Р№РґРµРЅ.

    :return: Р—РЅР°С‡РµРЅРёРµ РєР»СЋС‡Р°, РµСЃР»Рё РєР»СЋС‡ РЅР°Р№РґРµРЅ Рё РµРіРѕ Р·РЅР°С‡РµРЅРёРµ РІР°Р»РёРґРЅРѕ. Р•СЃР»Рё РєР»СЋС‡ РЅРµ РЅР°Р№РґРµРЅ Рё
    raise_ex_if_not_exists == False - РІРѕР·РІСЂР°С‰Р°РµС‚ None. Р’ Р»СЋР±РѕРј РґСЂСѓРіРѕРј СЃР»СѓС‡Р°Рµ РІРѕР·Р±СѓР¶РґР°РµС‚ РёСЃРєР»СЋС‡РµРЅРёСЏ.
    """
    if param_name not in list(section.keys()):
        if raise_if_not_exists:
            raise ParamNotFoundError(param_name)
        return None

    value = section[param_name].strip()

    # Р•СЃР»Рё Р·РЅР°С‡РµРЅРёРµ РїСѓСЃС‚РѕРµ ("", РѕРЅРѕ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ None)
    if not value:
        if valid_values and None in valid_values:
            return value
        raise EmptyValueError(param_name)

    if valid_values and valid_values != [None] and value not in valid_values:
        raise ValueNotValidError(param_name, value, valid_values)
    return value


def create_config_obj(config_path: str) -> ConfigParser:
    """
    РЎРѕР·РґР°РµС‚ РѕР±СЉРµРєС‚ РєРѕРЅС„РёРіР° СЃ РЅСѓР¶РЅС‹РјРё РЅР°СЃС‚СЂРѕР№РєР°РјРё.

    :param config_path: РїСѓС‚СЊ РґРѕ С„Р°Р№Р»Р° РєРѕРЅС„РёРіР°.

    :return: РѕР±СЉРµРєС‚ РєРѕРЅС„РёРіР°.
    """
    config = ConfigParser(delimiters=(":",), interpolation=None)
    config.optionxform = str
    config.read_file(codecs.open(config_path, "r", "utf8"))
    return config


def load_main_config(config_path: str):
    """
    РџР°СЂСЃРёС‚ Рё РїСЂРѕРІРµСЂСЏРµС‚ РЅР° РїСЂР°РІРёР»СЊРЅРѕСЃС‚СЊ РѕСЃРЅРѕРІРЅРѕР№ РєРѕРЅС„РёРі.

    :param config_path: РїСѓС‚СЊ РґРѕ РѕСЃРЅРѕРІРЅРѕРіРѕ РєРѕРЅС„РёРіР°.

    :return: СЃРїР°СЂСЃРµРЅС‹Р№ РѕСЃРЅРѕРІРЅРѕР№ РєРѕРЅС„РёРі.
    """
    config = create_config_obj(config_path)
    values = {
        "FunPay": {
            "golden_key": "any",
            "user_agent": "any+empty",
            "autoRaise": ["0", "1"],
            "autoResponse": ["0", "1"],
            "autoDelivery": ["0", "1"],
            "multiDelivery": ["0", "1"],
            "autoRestore": ["0", "1"],
            "autoDisable": ["0", "1"],
            "oldMsgGetMode": ["0", "1"],
            "keepSentMessagesUnread": ["0", "1"],
            "locale": ["ru", "en", "uk"]
        },

        "Telegram": {
            "enabled": ["0", "1"],
            "token": "any+empty",
            "secretKeyHash": "any",
            "proxy": "any+empty",
            "blockLogin": ["0", "1"]
        },

        "BlockList": {
            "blockDelivery": ["0", "1"],
            "blockResponse": ["0", "1"],
            "blockNewMessageNotification": ["0", "1"],
            "blockNewOrderNotification": ["0", "1"],
            "blockCommandNotification": ["0", "1"]
        },

        "NewMessageView": {
            "includeMyMessages": ["0", "1"],
            "includeFPMessages": ["0", "1"],
            "includeBotMessages": ["0", "1"],
            "notifyOnlyMyMessages": ["0", "1"],
            "notifyOnlyFPMessages": ["0", "1"],
            "notifyOnlyBotMessages": ["0", "1"],
            "showImageName": ["0", "1"]
        },

        "Greetings": {
            "ignoreSystemMessages": ["0", "1"],
            "onlyNewChats": ["0", "1"],
            "sendGreetings": ["0", "1"],
            "greetingsText": "any",
            "greetingsCooldown": "any"
        },

        "OrderConfirm": {
            "sendReply": ["0", "1"],
            "replyText": "any"
        },

        "ReviewReply": {
            "star1Reply": ["0", "1"],
            "star2Reply": ["0", "1"],
            "star3Reply": ["0", "1"],
            "star4Reply": ["0", "1"],
            "star5Reply": ["0", "1"],
            "star1ReplyText": "any+empty",
            "star2ReplyText": "any+empty",
            "star3ReplyText": "any+empty",
            "star4ReplyText": "any+empty",
            "star5ReplyText": "any+empty",
        },

        "Proxy": {
            "enable": ["0", "1"],
            "proxy": "any+empty",
            "check": ["0", "1"]
        },

        "Other": {
            "requestsDelay": [str(i) for i in range(1, 101)],
            "language": ["ru", "en", "uk"]
        }
    }

    for section_name in values:
        if section_name not in config.sections():
            raise ConfigParseError(config_path, section_name, SectionNotFoundError())

        # UPDATE
        if section_name == "Greetings" and "cacheInitChats" in config[section_name]:
            config.remove_option(section_name, "cacheInitChats")
            with open("configs/_main.cfg", "w", encoding="utf-8") as f:
                config.write(f)
        # END OF UPDATE

        for param_name in values[section_name]:

            # UPDATE
            if section_name == "FunPay" and param_name == "oldMsgGetMode" and param_name not in config[section_name]:
                config.set("FunPay", "oldMsgGetMode", "0")
                with open("configs/_main.cfg", "w", encoding="utf-8") as f:
                    config.write(f)
            elif section_name == "Greetings" and param_name == "ignoreSystemMessages" and param_name not in config[
                section_name]:
                config.set("Greetings", "ignoreSystemMessages", "0")
                with open("configs/_main.cfg", "w", encoding="utf-8") as f:
                    config.write(f)
            elif section_name == "Other" and param_name == "language" and param_name not in config[section_name]:
                config.set("Other", "language", "ru")
                with open("configs/_main.cfg", "w", encoding="utf-8") as f:
                    config.write(f)
            elif section_name == "Other" and param_name == "language" and config[section_name][param_name] == "eng":
                config.set("Other", "language", "en")
                with open("configs/_main.cfg", "w", encoding="utf-8") as f:
                    config.write(f)
            elif section_name == "Greetings" and param_name == "greetingsCooldown" and param_name not in config[
                section_name]:
                config.set("Greetings", "greetingsCooldown", "2")
                with open("configs/_main.cfg", "w", encoding="utf-8") as f:
                    config.write(f)
            elif section_name == "FunPay" and param_name == "keepSentMessagesUnread" and \
                    param_name not in config[section_name]:
                config.set("FunPay", "keepSentMessagesUnread", "0")
                with open("configs/_main.cfg", "w", encoding="utf-8") as f:
                    config.write(f)
            elif section_name == "NewMessageView" and param_name == "showImageName" and \
                    param_name not in config[section_name]:
                config.set("NewMessageView", "showImageName", "1")
                with open("configs/_main.cfg", "w", encoding="utf-8") as f:
                    config.write(f)
            elif section_name == "Telegram" and param_name == "blockLogin" and \
                    param_name not in config[section_name]:
                config.set("Telegram", "blockLogin", "0")
                with open("configs/_main.cfg", "w", encoding="utf-8") as f:
                    config.write(f)
            elif section_name == "Telegram" and param_name == "secretKeyHash" and \
                    param_name not in config[section_name]:
                config.set(section_name, "secretKeyHash", hash_password(config[section_name]["secretKey"]))
                config.remove_option(section_name, "secretKey")
                with open("configs/_main.cfg", "w", encoding="utf-8") as f:
                    config.write(f)
            elif section_name == "FunPay" and param_name == "locale" and \
                    param_name not in config[section_name]:
                config.set(section_name, "locale", "ru")
                with open("configs/_main.cfg", "w", encoding="utf-8") as f:
                    config.write(f)
            elif section_name == "Greetings" and param_name == "onlyNewChats" and param_name not in config[
                section_name]:
                config.set("Greetings", "onlyNewChats", "0")
                with open("configs/_main.cfg", "w", encoding="utf-8") as f:
                    config.write(f)
            elif section_name == "Proxy" and param_name == "proxy" and param_name not in config[section_name]:
                if config["Proxy"]["ip"] and config["Proxy"]["port"]:
                    config.set("Proxy", "proxy", "")
                else:
                    config.set("Proxy", "proxy", build_proxy(None, config["Proxy"]["login"],
                                                             config["Proxy"]["password"], config["Proxy"]["ip"],
                                                             config["Proxy"]["port"]))
                config.remove_option(section_name, "login")
                config.remove_option(section_name, "password")
                config.remove_option(section_name, "ip")
                config.remove_option(section_name, "port")
                with open("configs/_main.cfg", "w", encoding="utf-8") as f:
                    config.write(f)
            elif section_name == "Telegram" and param_name == "proxy" and param_name not in config[section_name]:
                config.set("Telegram", "proxy", "")
                with open("configs/_main.cfg", "w", encoding="utf-8") as f:
                    config.write(f)

            # END OF UPDATE

            try:
                if values[section_name][param_name] == "any":
                    check_param(param_name, config[section_name])
                elif values[section_name][param_name] == "any+empty":
                    check_param(param_name, config[section_name], valid_values=[None])
                else:
                    check_param(param_name, config[section_name], valid_values=values[section_name][param_name])
            except (ParamNotFoundError, EmptyValueError, ValueNotValidError) as e:
                raise ConfigParseError(config_path, section_name, e)

    return config


def load_auto_response_config(config_path: str):
    """
    РџР°СЂСЃРёС‚ Рё РїСЂРѕРІРµСЂСЏРµС‚ РЅР° РїСЂР°РІРёР»СЊРЅРѕСЃС‚СЊ РєРѕРЅС„РёРі РєРѕРјР°РЅРґ.

    :param config_path: РїСѓС‚СЊ РґРѕ РєРѕРЅС„РёРіР° РєРѕРјР°РЅРґ.

    :return: СЃРїР°СЂСЃРµРЅС‹Р№ РєРѕРЅС„РёРі РєРѕРјР°РЅРґ.
    """
    try:
        config = create_config_obj(config_path)
    except configparser.DuplicateSectionError as e:
        raise ConfigParseError(config_path, e.section, DuplicateSectionErrorWrapper())

    command_sets = []
    for command in config.sections():
        try:
            check_param("response", config[command])
            check_param("telegramNotification", config[command], valid_values=["0", "1"], raise_if_not_exists=False)
            check_param("enabled", config[command], valid_values=["0", "1"], raise_if_not_exists=False)
            check_param("notificationText", config[command], raise_if_not_exists=False)
        except (ParamNotFoundError, EmptyValueError, ValueNotValidError) as e:
            raise ConfigParseError(config_path, command, e)

        if not config.has_option(command, "enabled"):
            config.set(command, "enabled", "1")

        if "|" in command:
            command_sets.append(command)

    for command_set in command_sets:
        commands = command_set.split("|")
        parameters = config[command_set]

        for new_command in commands:
            new_command = new_command.strip()
            if not new_command:
                continue
            if new_command in config.sections():
                raise ConfigParseError(config_path, command_set, SubCommandAlreadyExists(new_command))
            config.add_section(new_command)
            for param_name in parameters:
                config.set(new_command, param_name, parameters[param_name])
    return config


def load_raw_auto_response_config(config_path: str):
    """
    Р—Р°РіСЂСѓР¶Р°РµС‚ РёСЃС…РѕРґРЅС‹Р№ РєРѕРЅС„РёРі Р°РІС‚РѕРѕС‚РІРµС‚С‡РёРєР°.

    :param config_path: РїСѓС‚СЊ РґРѕ РєРѕРЅС„РёРіР° РєРѕРјР°РЅРґ.

    :return: СЃРїР°СЂСЃРµРЅС‹Р№ РєРѕРЅС„РёРі РєРѕРјР°РЅРґ.
    """
    config = create_config_obj(config_path)
    for raw_commands in config.sections():
        if not config.has_option(raw_commands, "enabled"):
            config.set(raw_commands, "enabled", "1")
    return config


def load_auto_delivery_config(config_path: str):
    """
    РџР°СЂСЃРёС‚ Рё РїСЂРѕРІРµСЂСЏРµС‚ РЅР° РїСЂР°РІРёР»СЊРЅРѕСЃС‚СЊ РєРѕРЅС„РёРі Р°РІС‚РѕРІС‹РґР°С‡Рё.

    :param config_path: РїСѓС‚СЊ РґРѕ РєРѕРЅС„РёРіР° Р°РІС‚РѕРІС‹РґР°С‡Рё.

    :return: СЃРїР°СЂСЃРµРЅС‹Р№ РєРѕРЅС„РёРі С‚РѕРІР°СЂРѕРІ РґР»СЏ Р°РІС‚РѕРІС‹РґР°С‡Рё.
    """
    try:
        config = create_config_obj(config_path)
    except configparser.DuplicateSectionError as e:
        raise ConfigParseError(config_path, e.section, DuplicateSectionErrorWrapper())

    for lot_title in config.sections():
        try:
            lot_response = check_param("response", config[lot_title])
            products_file_name = check_param("productsFileName", config[lot_title], raise_if_not_exists=False)
            check_param("disable", config[lot_title], valid_values=["0", "1"], raise_if_not_exists=False)
            check_param("disableAutoRestore", config[lot_title], valid_values=["0", "1"], raise_if_not_exists=False)
            check_param("disableAutoDisable", config[lot_title], valid_values=["0", "1"], raise_if_not_exists=False)
            check_param("disableAutoDelivery", config[lot_title], valid_values=["0", "1"], raise_if_not_exists=False)
            if products_file_name is None:
                # Р•СЃР»Рё РґР°РЅРЅРѕРіРѕ РїР°СЂР°РјРµС‚СЂР° РЅРµС‚, С‚Рѕ РІ С‚РµРєСѓС‰РµРј Р»РѕС‚Рµ Р±РѕР»РµРµ РЅРµС‡РµРіРѕ РїСЂРѕРІРµСЂСЏС‚СЊ -> РїРµСЂРµС…РѕРґ РЅР° СЃР»РµРґ. РёС‚РµСЂР°С†РёСЋ.
                continue
        except (ParamNotFoundError, EmptyValueError, ValueNotValidError) as e:
            raise ConfigParseError(config_path, lot_title, e)

        # РџСЂРѕРІРµСЂСЏРµРј, СЃСѓС‰РµСЃС‚РІСѓРµС‚ Р»Рё С„Р°Р№Р».
        if not os.path.exists(f"storage/products/{products_file_name}"):
            raise ConfigParseError(config_path, lot_title,
                                   ProductsFileNotFoundError(f"storage/products/{products_file_name}"))

        # РџСЂРѕРІРµСЂСЏРµРј, РµСЃС‚СЊ Р»Рё С…РѕС‚СЏ Р±С‹ 1 РїРµСЂРµРјРµРЅРЅР°СЏ $product РІ С‚РµРєСЃС‚Рµ response.
        if "$product" not in lot_response:
            raise ConfigParseError(config_path, lot_title, NoProductVarError())
    return config
