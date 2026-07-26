from __future__ import annotations

from configparser import ConfigParser


DEFAULT_DISPLAY_CURRENCY = "UAH"
DEFAULT_UAH_RATE = 43.5
DEFAULT_FUNPAY_RUB_TO_USD_RATE = 80.521
DEFAULT_WITHDRAW_COMMISSION_PERCENT = 6.0


def get_display_currency(config: ConfigParser | None) -> str:
    if config and config.has_section("DisplayCurrency"):
        return config["DisplayCurrency"].get("currency", DEFAULT_DISPLAY_CURRENCY).strip().upper()
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
    return _get_positive_float(config, "withdrawCommissionPercent", DEFAULT_WITHDRAW_COMMISSION_PERCENT)


def format_amount(amount: int | float) -> str:
    value = round(float(amount), 2)
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def is_rub(currency) -> bool:
    return getattr(currency, "name", "").upper() == "RUB"


def rub_to_uah(amount: int | float, config: ConfigParser | None = None,
               include_withdraw_commission: bool = False) -> float:
    rub_amount = float(amount)
    if include_withdraw_commission:
        rub_amount *= max(0, 100 - get_withdraw_commission_percent(config)) / 100
    usdt_amount = rub_amount / get_funpay_rub_to_usd_rate(config)
    return usdt_amount * get_uah_rate(config)


def format_money(amount: int | float, money_currency, config: ConfigParser | None = None,
                 include_withdraw_commission: bool = False) -> str:
    if get_display_currency(config) == "UAH" and is_rub(money_currency):
        return f"{format_amount(rub_to_uah(amount, config, include_withdraw_commission))} UAH"
    return f"{format_amount(amount)} {money_currency}".strip()


def format_rub_as_display(amount: int | float, config: ConfigParser | None = None,
                          include_withdraw_commission: bool = False) -> str:
    if get_display_currency(config) == "UAH":
        return f"{format_amount(rub_to_uah(amount, config, include_withdraw_commission))} UAH"
    return f"{format_amount(amount)} RUB"


def format_balance_short(balance, config: ConfigParser | None = None) -> str:
    return f"{format_rub_as_display(balance.total_rub, config, True)}, {format_amount(balance.total_usd)} USD, {format_amount(balance.total_eur)} EUR"
