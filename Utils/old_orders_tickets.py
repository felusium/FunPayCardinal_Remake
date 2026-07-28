from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime
from http.cookies import SimpleCookie
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("FPC.old_orders_tickets")

SUPPORT_TICKETS_URL = "https://support.funpay.com/tickets"
SUPPORT_NEW_TICKET_URL = "https://support.funpay.com/tickets/new/1"
STATE_FILE = "storage/cache/ticket_orders_state.json"
TICKET_COOLDOWN_SECONDS = 24 * 60 * 60
MAX_ERROR_DETAILS_LEN = 3200
MAX_RESPONSE_PREVIEW_LEN = 900
MAX_SUPPORT_REDIRECTS = 8
MAX_429_RETRIES = 4
SUPPORT_HOST = "support.funpay.com"


def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {"last_sent_at": 0, "last_attempt_at": 0, "last_error": "", "last_orders": [], "pending": {}}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            state = json.load(file)
        if not isinstance(state, dict):
            raise ValueError("state is not a dict")
    except Exception:
        logger.warning("Не удалось прочитать state-файл тикетов старых заказов.")
        logger.debug("TRACEBACK", exc_info=True)
        return {"last_sent_at": 0, "last_attempt_at": 0, "last_error": "", "last_orders": [], "pending": {}}
    state.setdefault("last_sent_at", 0)
    state.setdefault("last_attempt_at", 0)
    state.setdefault("last_error", "")
    state.setdefault("last_orders", [])
    state.setdefault("pending", {})
    return state


def save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    tmp_path = f"{STATE_FILE}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=4)
    os.replace(tmp_path, STATE_FILE)


def format_dt(timestamp: int | float | None) -> str:
    if not timestamp:
        return "ніколи"
    return datetime.fromtimestamp(float(timestamp)).strftime("%d.%m.%Y %H:%M:%S")


def format_left(seconds: int | float) -> str:
    seconds = max(0, int(seconds))
    hours, seconds = divmod(seconds, 3600)
    minutes, _ = divmod(seconds, 60)
    if hours:
        return f"{hours} год {minutes} хв"
    return f"{minutes} хв"


def cooldown_left(state: dict) -> int:
    last_sent_at = int(state.get("last_sent_at", 0) or 0)
    if not last_sent_at:
        return 0
    return max(0, last_sent_at + TICKET_COOLDOWN_SECONDS - int(time.time()))


def get_old_orders_page(acc, start_from: str, subcs: dict | None, locale) -> tuple[str | None, list[str], str, dict]:
    attempts = 3
    while attempts:
        try:
            result = acc.get_sales(start_from=start_from or None, state="paid", locale=locale, sudcategories=subcs)
            break
        except Exception:
            attempts -= 1
            time.sleep(1)
    else:
        raise RuntimeError("Не вдалося отримати список замовлень.")

    old_orders = []
    for sale in result[1]:
        try:
            parser = BeautifulSoup(sale.html, "lxml")
            time_el = parser.find("div", {"class": "tc-date-time"})
            time_text = time_el.text if time_el else ""
        except Exception:
            time_text = ""

        if any(word in time_text for word in ("сегодня", "сьогодні", "today")):
            continue
        if (datetime.now() - sale.date).total_seconds() < 3600 * 24:
            continue
        old_orders.append(f"#{sale.id}")

    return result[0], old_orders, result[2], result[3]


def get_all_old_orders(acc) -> list[str]:
    start_from = ""
    old_orders = []
    locale = None
    subcs = None
    while start_from is not None:
        start_from, page_orders, locale, subcs = get_old_orders_page(acc, start_from, subcs, locale)
        old_orders.extend(page_orders)
        time.sleep(1)
    return old_orders


def normalize_text(value: str | None) -> str:
    return " ".join(str(value or "").casefold().split())


def limit_text(value: str, limit: int = MAX_ERROR_DETAILS_LEN) -> str:
    value = str(value or "").strip()
    if len(value) <= limit:
        return value
    return value[:limit - 3].rstrip() + "..."


def redact_sensitive_text(value: str | None) -> str:
    text = str(value or "")
    text = re.sub(r"jwt=[^&\s]+", "jwt=<hidden>", text, flags=re.IGNORECASE)
    text = re.sub(r"([?&](?:token|auth|key|signature|sig)=)[^&\s]+", r"\1<hidden>", text, flags=re.IGNORECASE)
    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "<email>", text)
    text = re.sub(r"\b[a-f0-9]{32,}\b", "<secret>", text, flags=re.IGNORECASE)
    return text


def response_visible_preview(response, limit: int = MAX_RESPONSE_PREVIEW_LEN) -> str:
    try:
        content = response.content or b""
        text = BeautifulSoup(content.decode(errors="ignore"), "lxml").get_text(" ", strip=True)
    except Exception:
        try:
            text = response.text
        except Exception:
            text = ""
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return limit_text(redact_sensitive_text(text), limit) if text else "-"


def response_details(response, reason: str, extra: list[str] | None = None) -> str:
    location = response.headers.get("Location") or "-"
    lines = [
        reason,
        f"HTTP: {getattr(response, 'status_code', '-')}",
        f"URL: {redact_sensitive_text(getattr(response, 'url', '-'))}",
        f"Location: {redact_sensitive_text(location)}",
        f"Content-Type: {response.headers.get('Content-Type') or '-'}"
    ]
    if extra:
        lines.extend(redact_sensitive_text(item) for item in extra)
    lines.append(f"Ответ страницы: {response_visible_preview(response)}")
    return limit_text("\n".join(lines))


def redirect_debug_lines(redirects: list[str]) -> list[str]:
    if not redirects:
        return []
    return ["Редиректы:"] + [f"- {redact_sensitive_text(item)}" for item in redirects[-8:]]


def support_cookie_names(acc) -> list[str]:
    names = []
    for cookie in getattr(acc.session, "cookies", []):
        domain = str(getattr(cookie, "domain", "") or "")
        if SUPPORT_HOST in domain:
            path = str(getattr(cookie, "path", "") or "/")
            names.append(f"{cookie.name}(domain={domain}, path={path})")
    return sorted(set(names))


def support_cookie_debug_line(acc) -> str:
    names = support_cookie_names(acc)
    return "Support cookies: " + (", ".join(names) if names else "-")


def support_ticket_cookie_debug_line(acc) -> str:
    names = []
    for cookie in getattr(acc.session, "cookies", []):
        domain = str(getattr(cookie, "domain", "") or "")
        path = str(getattr(cookie, "path", "") or "/")
        normalized_domain = domain.lstrip(".")
        domain_ok = normalized_domain == SUPPORT_HOST
        path_ok = "/tickets/new/1".startswith(path.rstrip("/") or "/")
        if domain_ok and path_ok:
            names.append(f"{cookie.name}(domain={domain}, path={path})")
    names = sorted(set(names))
    return "Cookies for /tickets/new/1: " + (", ".join(names) if names else "-")


def clear_support_cookies(acc, name: str | None = None) -> None:
    jar = getattr(acc.session, "cookies", None)
    if jar is None:
        return
    for cookie in list(jar):
        domain = str(getattr(cookie, "domain", "") or "")
        if SUPPORT_HOST not in domain:
            continue
        if name is not None and cookie.name != name:
            continue
        try:
            jar.clear(cookie.domain, cookie.path, cookie.name)
        except Exception:
            pass


def form_debug_lines(form, payload: dict, flags: dict[str, bool], submit_url: str, method: str) -> list[str]:
    field_names = sorted(str(name) for name in payload)
    if len(field_names) > 35:
        names_text = ", ".join(field_names[:35]) + f", ... (+{len(field_names) - 35})"
    else:
        names_text = ", ".join(field_names) or "-"
    flags_text = ", ".join(f"{name}={'yes' if ok else 'no'}" for name, ok in flags.items())
    return [
        f"Форма: method={method.upper()} action={submit_url}",
        f"Поля формы: {len(payload)} ({names_text})",
        f"Заполнение: {flags_text}"
    ]


def get_funpay_cookies(acc) -> dict:
    cookies = {"golden_key": acc.golden_key, "cookie_prefs": "1"}
    cookies.update(getattr(acc, "cookies", {}) or {})
    if getattr(acc, "phpsessid", None):
        cookies["PHPSESSID"] = acc.phpsessid
    return cookies


def get_request_cookies(acc, url: str) -> dict | None:
    parsed = urlparse(url)
    if parsed.netloc.endswith("funpay.com") and not parsed.netloc.endswith("support.funpay.com"):
        return get_funpay_cookies(acc)
    return None


def get_support_session_cookies(acc, url: str) -> dict:
    parsed = urlparse(url)
    request_path = parsed.path or "/"
    cookies = {}
    for cookie in getattr(acc.session, "cookies", []):
        domain = str(getattr(cookie, "domain", "") or "")
        path = str(getattr(cookie, "path", "") or "/")
        if domain.lstrip(".") != SUPPORT_HOST:
            continue
        if not request_path.startswith(path.rstrip("/") or "/"):
            continue
        cookies[cookie.name] = cookie.value
    return cookies


def persist_response_cookies(acc, response) -> None:
    host = urlparse(getattr(response, "url", "") or "").hostname
    if not host:
        return

    for cookie in response.cookies:
        domain = cookie.domain or host
        path = cookie.path or "/"
        if host == SUPPORT_HOST:
            clear_support_cookies(acc, cookie.name)
            acc.session.cookies.set(cookie.name, cookie.value, domain=SUPPORT_HOST, path="/")
        else:
            acc.session.cookies.set(cookie.name, cookie.value, domain=domain, path=path)

    set_cookie_header = response.headers.get("Set-Cookie")
    if not set_cookie_header:
        return
    try:
        parsed = SimpleCookie()
        parsed.load(set_cookie_header)
    except Exception:
        return

    for name, morsel in parsed.items():
        domain = morsel["domain"] or host
        path = morsel["path"] or "/"
        if host == SUPPORT_HOST:
            clear_support_cookies(acc, name)
            acc.session.cookies.set(name, morsel.value, domain=SUPPORT_HOST, path="/")
        else:
            acc.session.cookies.set(name, morsel.value, domain=domain, path=path)


def support_request(acc, method: str, url: str, headers: dict | None = None,
                    data: dict | None = None, allow_redirects: bool = False):
    req_headers = {
        "accept-language": "uk-UA,uk;q=0.9,ru;q=0.8,en-US;q=0.7,en;q=0.6",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "referer": SUPPORT_TICKETS_URL,
        "user-agent": getattr(acc, "user_agent", None) or
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
    req_headers.update(headers or {})
    parsed = urlparse(url)
    request_kwargs = {
        "method": method,
        "url": url,
        "headers": req_headers,
        "data": data or {},
        "timeout": getattr(acc, "requests_timeout", 10),
        "proxies": getattr(acc, "proxy", None) or {},
        "allow_redirects": allow_redirects
    }
    if parsed.netloc == SUPPORT_HOST:
        request_kwargs["cookies"] = get_support_session_cookies(acc, url)
        response = requests.request(**request_kwargs)
    else:
        request_kwargs["cookies"] = get_request_cookies(acc, url)
        response = acc.session.request(**request_kwargs)
    persist_response_cookies(acc, response)
    return response


def request_with_429_backoff(acc, method: str, url: str, headers: dict | None = None,
                             data: dict | None = None, allow_redirects: bool = False):
    response = None
    for attempt in range(MAX_429_RETRIES):
        response = support_request(acc, method, url, headers, data, allow_redirects)
        if response.status_code != 429:
            return response
        if attempt + 1 < MAX_429_RETRIES:
            time.sleep(min(2 ** attempt, 8))
    return response


def same_site_referer(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.endswith("support.funpay.com"):
        return SUPPORT_TICKETS_URL
    return "https://funpay.com/"


def follow_support_redirects(acc, url: str) -> tuple[object, list[str]]:
    current_url = url
    redirects = []
    seen = {}
    for _ in range(MAX_SUPPORT_REDIRECTS):
        response = request_with_429_backoff(
            acc,
            "get",
            current_url,
            {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "referer": same_site_referer(current_url)
            }
        )
        if response.status_code == 429:
            return response, redirects
        location = response.headers.get("Location", "")
        if not (300 <= response.status_code < 400) or not location:
            return response, redirects
        next_url = urljoin(current_url, location)
        redirects.append(f"{response.status_code}: {current_url} -> {next_url}")
        base_next_url = next_url.split("?", 1)[0]
        seen[base_next_url] = seen.get(base_next_url, 0) + 1
        if base_next_url == SUPPORT_NEW_TICKET_URL and seen[base_next_url] >= 3:
            return response, redirects + [
                "Остановлено: SSO-цикл вернул обратно на форму поддержки несколько раз.",
                support_cookie_debug_line(acc),
                support_ticket_cookie_debug_line(acc)
            ]
        current_url = next_url
    return response, redirects + [
        f"Остановлено: слишком много редиректов после {current_url}",
        support_cookie_debug_line(acc),
        support_ticket_cookie_debug_line(acc)
    ]


def open_support_ticket_form(acc) -> tuple[object, list[str]]:
    clear_support_cookies(acc)
    response, redirects = follow_support_redirects(acc, SUPPORT_NEW_TICKET_URL)
    if response.status_code == 429 and "/support/sso" in response.url:
        try:
            acc.get(update_phpsessid=True)
            redirects.append("Обновлен PHPSESSID через FunPay, повтор открытия формы поддержки.")
        except Exception as exc:
            redirects.append(f"Не удалось обновить PHPSESSID перед повтором: {type(exc).__name__}: {exc}")
        time.sleep(2)
        retry_response, retry_redirects = follow_support_redirects(acc, SUPPORT_NEW_TICKET_URL)
        redirects.extend(retry_redirects)
        response = retry_response
    redirects.append(support_cookie_debug_line(acc))
    redirects.append(support_ticket_cookie_debug_line(acc))
    return response, redirects


def extract_form_payload(form) -> dict:
    payload = {}
    for field in form.find_all(["input", "textarea", "select"]):
        name = field.get("name")
        if not name:
            continue
        if field.name == "input":
            field_type = (field.get("type") or "text").lower()
            if field_type in ("submit", "button", "image", "file"):
                continue
            if field_type in ("checkbox", "radio") and not field.has_attr("checked"):
                continue
            payload[name] = field.get("value", "")
        elif field.name == "textarea":
            payload[name] = field.text or ""
        elif field.name == "select":
            selected = field.find("option", selected=True) or field.find("option")
            payload[name] = selected.get("value", "") if selected else ""
    return payload


def control_name_for_label(form, label) -> str | None:
    if label.get("for"):
        control = form.find(id=label["for"])
    else:
        control = label.find(["input", "textarea", "select"])
        if control is None and label.parent:
            control = label.parent.find(["input", "textarea", "select"])
    return control.get("name") if control and control.get("name") else None


def set_by_label(form, payload: dict, label_parts: list[str], value: str) -> bool:
    parts = [normalize_text(part) for part in label_parts]
    for label in form.find_all("label"):
        label_text = normalize_text(label.get_text(" ", strip=True))
        if any(part in label_text for part in parts):
            name = control_name_for_label(form, label)
            if name:
                payload[name] = value
                return True
    return False


def set_by_name_part(form, payload: dict, name_parts: list[str], value: str) -> bool:
    parts = [normalize_text(part) for part in name_parts]
    for field in form.find_all(["input", "textarea"]):
        name = field.get("name")
        if name and any(part in normalize_text(name) for part in parts):
            payload[name] = value
            return True
    return False


def set_first_textarea(form, payload: dict, value: str) -> bool:
    for field in form.find_all("textarea"):
        name = field.get("name")
        if name:
            payload[name] = value
            return True
    return False


def choose_radio_by_label(form, payload: dict, label_parts: list[str]) -> bool:
    parts = [normalize_text(part) for part in label_parts]
    for label in form.find_all("label"):
        label_text = normalize_text(label.get_text(" ", strip=True))
        if not any(part in label_text for part in parts):
            continue
        control = form.find(id=label["for"]) if label.get("for") else None
        if control is None:
            control = label.find("input", {"type": "radio"}) or (label.parent and label.parent.find("input", {"type": "radio"}))
        if control and control.get("name"):
            payload[control["name"]] = control.get("value", "1")
            return True
    return False


def choose_select_option(form, payload: dict, option_parts: list[str]) -> bool:
    parts = [normalize_text(part) for part in option_parts]
    for select in form.find_all("select"):
        name = select.get("name")
        if not name:
            continue
        for option in select.find_all("option"):
            option_text = normalize_text(option.get_text(" ", strip=True))
            if any(part in option_text for part in parts):
                payload[name] = option.get("value", "")
                return True
    return False


def create_support_ticket(acc, orders: list[str]) -> str:
    order_field = ", ".join(orders)
    orders_body = "\n".join(orders)
    response, redirects = open_support_ticket_form(acc)
    redirect_debug = redirect_debug_lines(redirects)
    if "account/login" in response.url:
        raise RuntimeError(response_details(response, "FunPay отправил на страницу входа. Обнови golden_key/PHPSESSID.", redirect_debug))
    if response.status_code == 429:
        raise RuntimeError(response_details(response, "Не удалось открыть форму поддержки: SSO/FunPay вернул HTTP 429. Бот уже попробовал открыть именно support.funpay.com/tickets/new/1 и обновить PHPSESSID.", redirect_debug))
    if response.status_code != 200:
        raise RuntimeError(response_details(response, "Не удалось открыть форму поддержки.", redirect_debug))

    parser = BeautifulSoup(response.content.decode(errors="ignore"), "lxml")
    form = parser.find("form")
    if form is None:
        raise RuntimeError(response_details(response, "Не удалось найти форму заявки на странице поддержки.", redirect_debug))

    payload = extract_form_payload(form)
    action = form.get("action") or SUPPORT_NEW_TICKET_URL
    submit_url = urljoin(SUPPORT_NEW_TICKET_URL, action)
    method = (form.get("method") or "post").lower()

    filled_login = set_by_label(form, payload, ["ник", "логин", "nickname", "login"], str(getattr(acc, "username", "") or ""))
    filled_order = set_by_label(form, payload, ["номер замовлення", "номер заказа", "order"], order_field)
    filled_seller = choose_radio_by_label(form, payload, ["продавец", "продавець", "seller"])
    filled_problem = choose_select_option(form, payload, ["проблема із замовленням", "проблема с заказом", "order problem"])
    filled_topic = choose_select_option(form, payload, ["покупатель забыл подтвердить заказ", "покупець забув підтвердити"])
    filled_text = set_by_label(form, payload, ["текст", "опис", "сообщ", "повідом", "message"], orders_body)
    if not filled_text:
        filled_text = set_by_name_part(form, payload, ["message", "comment", "content", "text", "body"], orders_body)
    if not filled_text:
        filled_text = set_first_textarea(form, payload, orders_body)

    debug = form_debug_lines(form, payload, {
        "login": filled_login,
        "orders": filled_order,
        "seller": filled_seller,
        "problem": filled_problem,
        "topic": filled_topic,
        "text": filled_text
    }, submit_url, method)
    submit = support_request(
        acc,
        method,
        submit_url,
        {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://support.funpay.com",
            "referer": SUPPORT_NEW_TICKET_URL
        },
        payload
    )
    location = submit.headers.get("Location", "")
    if submit.status_code in (301, 302, 303) and location:
        return urljoin(SUPPORT_NEW_TICKET_URL, location)
    if submit.status_code == 429:
        raise RuntimeError(response_details(submit, "support.funpay.com вернул HTTP 429 при отправке. Это лимит сайта поддержки, бот паузу не ставит.", debug))
    if submit.status_code == 200 and "tickets/new" not in submit.url:
        return submit.url
    raise RuntimeError(response_details(submit, "FunPay не подтвердил создание тикета после отправки формы.", debug))
