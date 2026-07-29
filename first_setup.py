"""
В данном модуле написана подпрограмма первичной настройки FunPayCardinal'а.
"""

import os
from configparser import ConfigParser
import time
import telebot
from colorama import Fore, Style
from Utils.cardinal_tools import validate_proxy, hash_password, build_proxy, check_proxy
from Utils.config_loader import load_main_config

# locale#locale#locale
default_config = {
    "FunPay": {
        "golden_key": "",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "autoRaise": "0",
        "autoResponse": "0",
        "autoDelivery": "0",
        "multiDelivery": "0",
        "autoRestore": "0",
        "autoDisable": "0",
        "oldMsgGetMode": "0",
        "locale": "uk"
    },
    "Telegram": {
        "enabled": "0",
        "token": "",
        "secretKeyHash": "ХешСекретногоПароля",
        "blockLogin": "0",
        "proxy": ""
    },

    "BlockList": {
        "blockDelivery": "0",
        "blockResponse": "0",
        "blockNewMessageNotification": "0",
        "blockNewOrderNotification": "0",
        "blockCommandNotification": "0"
    },

    "NewMessageView": {
        "includeMyMessages": "1",
        "includeFPMessages": "1",
        "includeBotMessages": "0",
        "notifyOnlyMyMessages": "0",
        "notifyOnlyFPMessages": "0",
        "notifyOnlyBotMessages": "0",
        "showImageName": "1"
    },

    "Greetings": {
        "ignoreSystemMessages": "0",
        "onlyNewChats": "0",
        "sendGreetings": "0",
        "greetingsText": "Привіт, $chat_name!",
        "greetingsCooldown": "2"
    },

    "OrderConfirm": {
        "sendReply": "0",
        "replyText": "$username, дякую за підтвердження замовлення $order_id!\nЯкщо не складно, залиш, будь ласка, відгук!"
    },

    "ReviewReply": {
        "star1Reply": "0",
        "star2Reply": "0",
        "star3Reply": "0",
        "star4Reply": "0",
        "star5Reply": "0",
        "star1ReplyText": "",
        "star2ReplyText": "",
        "star3ReplyText": "",
        "star4ReplyText": "",
        "star5ReplyText": "",
    },

    "DisplayCurrency": {
        "currency": "UAH",
        "uahRate": "43.5",
        "funpayRubToUsdRate": "80.521",
        "funpayUahRubRate": "0.543",
        "funpayRateUpdatedAt": "0",
        "withdrawCommissionPercent": "0"
    },

    "Other": {
        "requestsDelay": "4",
        "language": "uk"
    }
}


def create_configs():
    if not os.path.exists("configs/auto_response.cfg"):
        with open("configs/auto_response.cfg", "w", encoding="utf-8"):
            ...

    if not os.path.exists("configs/auto_delivery.cfg"):
        with open("configs/auto_delivery.cfg", "w", encoding="utf-8"):
            ...


def create_config_obj(settings) -> ConfigParser:
    """
    Создает объект конфига с нужными настройками.

    :param settings: dict настроек.

    :return: объект конфига.
    """
    config = ConfigParser(delimiters=(":",), interpolation=None)
    config.optionxform = str
    config.read_dict(settings)
    return config


def contains_russian(text: str) -> bool:
    for char in text:
        if 'А' <= char <= 'я' or char in 'Ёё':
            return True
    return False

def input_proxy(set_telebot_proxy: bool = False) -> str | None:
    while True:
        proxy_input = input(f"{Fore.MAGENTA}{Style.BRIGHT}└───> {Style.RESET_ALL}").strip()

        if not proxy_input:
            if set_telebot_proxy:
                telebot.apihelper.proxy = None
            return None

        try:
            scheme, login, password, ip, port = validate_proxy(proxy_input)
            proxy = build_proxy(scheme, login, password, ip, port)

            if not check_proxy({"http": proxy, "https": proxy}):
                print("\nНевалідні проксі. Спробуй ще раз!")
                continue

            if set_telebot_proxy:
                telebot.apihelper.proxy = {"http": proxy, "https": proxy}

            return proxy

        except Exception as ex:
            print(f"\nНеправильний формат проксі: {ex}. Спробуй ще раз!")

def setup_telegram_proxy():
    config = load_main_config("configs/_main.cfg")
    print(
        f"\n{Fore.MAGENTA}{Style.BRIGHT}┌── {Fore.CYAN}" f"Якщо хочеш використовувати IPv4 проксі ДЛЯ ДОСТУПУ ДО TELEGRAM"
        f" – вкажи їх у форматі scheme://login:password@ip:port, login:password@ip:port або ip:port."
        f" Якщо ти не знаєш, " f"що це таке або вони тобі не потрібні - просто натисни Enter. "
        f"{Fore.RED}(* ^ ω ^){Style.RESET_ALL}")
    while True:
        try:
            proxy = input_proxy(set_telebot_proxy=True)
            username = telebot.TeleBot(config["Telegram"]["token"]).get_me().username
            print(f"\n\n{Fore.CYAN}Підключення до Telegram успішне: @{username}...{Style.RESET_ALL}")
            break
        except Exception as ex:
            print(f"\n\n{Fore.CYAN}Не вдалося додати проксі: {ex}...{Style.RESET_ALL}")

    config.set("Telegram", "proxy", proxy or "")
    print(f"{Fore.CYAN}Зберігаю конфіг...{Style.RESET_ALL}")
    with open("configs/_main.cfg", "w", encoding="utf-8") as f:
        config.write(f)
    time.sleep(5)


def first_setup():
    config = create_config_obj(default_config)
    sleep_time = 1

    print(f"{Fore.CYAN}{Style.BRIGHT}Привіт! {Fore.RED}(`-`)/{Style.RESET_ALL}")
    time.sleep(sleep_time)

    print(f"\n{Fore.CYAN}{Style.BRIGHT}Не можу знайти основний конфіг... {Fore.RED}(-_-;). . .{Style.RESET_ALL}")
    time.sleep(sleep_time)

    print(f"\n{Fore.CYAN}{Style.BRIGHT}Давай проведемо первинне налаштування! {Fore.RED}°++°{Style.RESET_ALL}")
    time.sleep(sleep_time)

    while True:
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}┌── {Fore.CYAN}"
              f"Для початку введи токен (golden_key) твого FunPay акаунта (його можна подивитися в розширенні EditThisCookie) {Fore.RED}(._.){Style.RESET_ALL}")
        golden_key = input(f"{Fore.MAGENTA}{Style.BRIGHT}└───> {Style.RESET_ALL}").strip()
        if len(golden_key) != 32:
            print(
                f"\n{Fore.CYAN}{Style.BRIGHT}Неправильний формат токена. Спробуй ще раз! {Fore.RED}\\(!!˚0˚)/{Style.RESET_ALL}")
            continue
        config.set("FunPay", "golden_key", golden_key)
        break

    while True:
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}┌── {Fore.CYAN}"
              f"Якщо хочеш, можеш вказати свій User-agent (введи в Google \"my user agent\"). Або можеш просто натиснути Enter. "
              f"{Fore.RED}¯\\(°_o)/¯{Style.RESET_ALL}")
        user_agent = input(f"{Fore.MAGENTA}{Style.BRIGHT}└───> {Style.RESET_ALL}").strip()
        if contains_russian(user_agent):
            print(
                f"\n{Fore.CYAN}{Style.BRIGHT}Ти не знаєш, що таке Google? {Fore.RED}\\(!!˚0˚)/{Style.RESET_ALL}")
            continue
        if user_agent:
            config.set("FunPay", "user_agent", user_agent)
        break

    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}┌── {Fore.CYAN}" f"Якщо хочеш використовувати IPv4 проксі ДЛЯ ДОСТУПУ ДО TELEGRAM"
          f" – вкажи їх у форматі scheme://login:password@ip:port, login:password@ip:port або ip:port."
          f" Якщо ти не знаєш, " f"що це таке або вони тобі не потрібні - просто натисни Enter. " 
          f"{Fore.RED}(* ^ ω ^){Style.RESET_ALL}")
    proxy = input_proxy(set_telebot_proxy=True)

    if proxy:
        config.set("Telegram", "proxy", proxy)


    while True:
        print(
            f"\n{Fore.MAGENTA}{Style.BRIGHT}┌── {Fore.CYAN}Введи API-токен Telegram-бота (його можна отримати у @BotFather). "
            f"{Fore.RED}(._.){Style.RESET_ALL}")
        token = input(f"{Fore.MAGENTA}{Style.BRIGHT}└───> {Style.RESET_ALL}").strip()
        try:
            if not token or not token.split(":")[0].isdigit():
                raise Exception("Неправильний формат токена")
            username = telebot.TeleBot(token).get_me().username
        except Exception as ex:
            s = ""
            if str(ex):
                s = f" ({str(ex)})"
            print(f"\n{Fore.CYAN}{Style.BRIGHT}Спробуй ще раз!{s} {Fore.RED}\\(!!˚0˚)/{Style.RESET_ALL}")
            continue
        break

    while True:
        print(
            f"\n{Fore.MAGENTA}{Style.BRIGHT}┌── {Fore.CYAN}Придумай пароль (його попросить Telegram-бот). Пароль має містити понад 8 символів, великі й малі літери та хоча б одну цифру "
            f" {Fore.RED}ᴖ̮ ̮ᴖ{Style.RESET_ALL}")
        password = input(f"{Fore.MAGENTA}{Style.BRIGHT}└───> {Style.RESET_ALL}").strip()
        if len(password) < 8 or password.lower() == password or password.upper() == password or not any(
                [i.isdigit() for i in password]):
            print(
                f"\n{Fore.CYAN}{Style.BRIGHT}Це слабкий пароль. Спробуй ще раз! {Fore.RED}\\(!!˚0˚)/{Style.RESET_ALL}")
            continue
        break

    config.set("Telegram", "enabled", "1")
    config.set("Telegram", "token", token)
    config.set("Telegram", "secretKeyHash", hash_password(password))

    print(f"\n{Fore.CYAN}{Style.BRIGHT}Готово! Зараз я збережу конфіг і завершу програму! "
          f"{Fore.RED}ʘ>ʘ{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}Запусти мене знову і напиши своєму Telegram-боту. "
          f"Усе інше ти зможеш налаштувати через нього. {Fore.RED}ʕ•ᴥ•ʔ{Style.RESET_ALL}")
    with open("configs/_main.cfg", "w", encoding="utf-8") as f:
        config.write(f)
    time.sleep(10)

