from __future__ import annotations

from configparser import ConfigParser


DEFAULT_DISPLAY_CURRENCY = "UAH"
DEFAULT_RUB_TO_UAH_RATE = 0.58


def get_display_currency(config: ConfigParser | None) -> str:
    if config and config.has_section("DisplayCurrency"):
        return config["DisplayCurrency"].get("currency", DEFAULT_DISPLAY_CURRENCY).strip().upper()
    return DEFAULT_DISPLAY_CURRENCY


def get_rub_to_uah_rate(config: ConfigParser | None) -> float:
    if config and config.has_section("DisplayCurrency"):
        raw_rate = config["DisplayCurrency"].get("rubToUahRate", str(DEFAULT_RUB_TO_UAH_RATE)).strip()
        try:
            rate = float(raw_rate.replace(",", "."))
            if rate > 0:
                return rate
        except ValueError:
            pass
    return DEFAULT_RUB_TO_UAH_RATE


def format_amount(amount: int | float) -> str:
    value = round(float(amount), 2)
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def is_rub(currency) -> bool:
    return getattr(currency, "name", "").upper() == "RUB"


def format_money(amount: int | float, currency, config: ConfigParser | None = None) -> str:
    if get_display_currency(config) == "UAH" and is_rub(currency):
        return f"{format_amount(float(amount) * get_rub_to_uah_rate(config))} ₴"
    return f"{format_amount(amount)} {currency}".strip()


def format_rub_as_display(amount: int | float, config: ConfigParser | None = None) -> str:
    if get_display_currency(config) == "UAH":
        return f"{format_amount(float(amount) * get_rub_to_uah_rate(config))} ₴"
    return f"{format_amount(amount)} ₽"


def format_balance_short(balance, config: ConfigParser | None = None) -> str:
    return f"{format_rub_as_display(balance.total_rub, config)}, {format_amount(balance.total_usd)} $, {format_amount(balance.total_eur)} €"
