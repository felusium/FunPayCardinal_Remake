from __future__ import annotations

import asyncio
import getpass
import json
import os
import subprocess
import sys
from configparser import ConfigParser
from urllib.parse import unquote, urlparse


CONFIG_FILE = os.path.join("plugins", "telegram_gifts_config.json")
MAIN_CONFIG_FILE = os.path.join("configs", "_main.cfg")


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        raise SystemExit(
            "Не найден plugins/telegram_gifts_config.json.\n"
            "Сначала запусти FPCR с плагином хотя бы один раз, чтобы он создал конфиг."
        )
    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_config(config: dict) -> None:
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=4, ensure_ascii=False)


def ensure_dependencies():
    try:
        import socks  # type: ignore
        from telethon import TelegramClient, errors  # type: ignore
    except ImportError:
        print("Устанавливаю зависимости Telethon/pysocks...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "telethon>=1.44.0", "pysocks"])
        import socks  # type: ignore
        from telethon import TelegramClient, errors  # type: ignore
    return TelegramClient, errors, socks


def get_telegram_proxy(config: dict, socks_module):
    if not config.get("use_telegram_proxy", True):
        return None
    parser = ConfigParser()
    parser.read(MAIN_CONFIG_FILE, encoding="utf-8")
    proxy_url = parser.get("Telegram", "proxy", fallback="").strip()
    if not proxy_url:
        return None

    parsed = urlparse(proxy_url)
    if not parsed.scheme or not parsed.hostname or not parsed.port:
        print(f"Telegram-прокси пропущен: неподдерживаемый формат {proxy_url!r}.")
        return None

    scheme = parsed.scheme.lower()
    if scheme.startswith("socks5"):
        proxy_type = socks_module.SOCKS5
    elif scheme.startswith("socks4"):
        proxy_type = socks_module.SOCKS4
    elif scheme in ("http", "https"):
        proxy_type = socks_module.HTTP
    else:
        print(f"Telegram-прокси пропущен: неподдерживаемая схема {scheme!r}.")
        return None

    username = unquote(parsed.username) if parsed.username else None
    password = unquote(parsed.password) if parsed.password else None
    return (proxy_type, parsed.hostname, parsed.port, True, username, password)


async def main() -> None:
    config = load_config()
    TelegramClient, errors, socks_module = ensure_dependencies()

    api_id = int(config.get("api_id", 0) or 0)
    api_hash = str(config.get("api_hash", "") or "").strip()
    if not api_id:
        api_id = int(input("api_id: ").strip())
        config["api_id"] = api_id
    if not api_hash:
        api_hash = getpass.getpass("api_hash: ").strip()
        config["api_hash"] = api_hash

    phone = str(config.get("phone", "") or "").strip()
    if not phone:
        phone = input("Телефон в международном формате (+380...): ").strip()
        config["phone"] = phone

    session_name = str(config.get("session_name", "plugins/telegram_gifts_session") or "plugins/telegram_gifts_session")
    os.makedirs(os.path.dirname(session_name) or ".", exist_ok=True)

    client = TelegramClient(
        session_name,
        api_id,
        api_hash,
        proxy=get_telegram_proxy(config, socks_module),
        receive_updates=False,
        sequential_updates=True,
        device_model="FPCR Gifts",
        system_version="Console login",
        app_version="1.0"
    )

    print("\nВажно: код входа вводи только здесь, в консоли. Не отправляй его в Telegram-чат.")
    await client.connect()
    try:
        if await client.is_user_authorized():
            print("Telegram-сессия уже авторизована.")
            save_config(config)
            return

        sent = await client.send_code_request(phone)
        code = input("Код Telegram: ").strip().replace(" ", "")
        try:
            await client.sign_in(phone=phone, code=code, phone_code_hash=sent.phone_code_hash)
        except errors.SessionPasswordNeededError:
            password = getpass.getpass("Пароль 2FA: ")
            await client.sign_in(password=password)

        if not await client.is_user_authorized():
            raise RuntimeError("Telethon не подтвердил авторизацию.")

        save_config(config)
        print(f"Готово. Сессия сохранена: {session_name}.session")
        print("Теперь перезапусти FPCR и проверь /tg_gifts_balance.")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
