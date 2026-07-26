from __future__ import annotations

from configparser import ConfigParser


DEFAULT_DISPLAY_CURRENCY = "UAH"
DEFAULT_UAH_RATE = 43.5
DEFAULT_FUNPAY_RUB_TO_USD_RATE = 80.521
DEFAULT_WITHDRAW_COMMISSION_PERCENT = 0.0


def get_display_currency(config: ConfigParser | None) -> str:
    return DEFAULT_DISPLAY_CURRENCY


def _get_positive_float(config: ConfigParser | None, key: str, default: float) -> float:
    if config and config.has_section("DisplayCurrency"):
        raw_value = config["DisplayCurrency"].get(key, str(default)).strip()
        try:
            value = float(raw_value.replace(",", "."))
            if value > 0:
                return value
        except ValueError:
            pass
    return default


def get_uah_rate(config: ConfigParser | None) -> float:
    return _get_positive_float(config, "uahRate", DEFAULT_UAH_RATE)


def get_funpay_rub_to_usd_rate(config: ConfigParser | None) -> float:
    return _get_positive_float(config, "funpayRubToUsdRate", DEFAULT_FUNPAY_RUB_TO_USD_RATE)


def get_withdraw_commission_percent(config: ConfigParser | None) -> float:
    return DEFAULT_WITHDRAW_COMMISSION_PERCENT


def format_amount(amount: int | float) -> str:
    value = round(float(amount), 2)
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def is_rub(currency) -> bool:
    return getattr(currency, "name", "").upper() == "RUB"


def is_usd(currency) -> bool:
    return getattr(currency, "name", "").upper() in ("USD", "USDT")


def rub_to_uah(amount: int | float, config: ConfigParser | None = None,
               include_withdraw_commission: bool = False) -> float:
    rub_amount = float(amount)
    usdt_amount = rub_amount / get_funpay_rub_to_usd_rate(config)
    return usdt_amount * get_uah_rate(config)


def format_money(amount: int | float, money_currency, config: ConfigParser | None = None,
                 include_withdraw_commission: bool = False) -> str:
    if is_rub(money_currency):
        return f"{format_amount(rub_to_uah(amount, config, include_withdraw_commission))} UAH"
    if is_usd(money_currency):
        return f"{format_amount(float(amount) * get_uah_rate(config))} UAH"
    return f"{format_amount(amount)} UAH"


def format_rub_as_display(amount: int | float, config: ConfigParser | None = None,
                          include_withdraw_commission: bool = False) -> str:
    return f"{format_amount(rub_to_uah(amount, config, include_withdraw_commission))} UAH"


def format_balance_short(balance, config: ConfigParser | None = None) -> str:
    return format_rub_as_display(balance.total_rub, config, False)
