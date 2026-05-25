import logging
import time as _time
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# ── Live exchange-rate helper ───────────────────
_rate_cache: dict = {"rate": None, "fetched_at": 0}
_RATE_CACHE_TTL = 120  # 2 minutes


class ExchangeRateUnavailable(Exception):
    """Raised when no live exchange rate can be obtained."""
    pass


def get_tzs_per_usd() -> float:
    """Return the current TZS/USD rate, fetched live with a 2-minute cache.
    Raises ExchangeRateUnavailable if no rate can be obtained — never guesses."""
    now = _time.time()
    if _rate_cache["rate"] and (now - _rate_cache["fetched_at"]) < _RATE_CACHE_TTL:
        return _rate_cache["rate"]

    # Primary API
    try:
        resp = requests.get(
            "https://open.er-api.com/v6/latest/USD", timeout=5
        )
        data = resp.json()
        if data.get("result") == "success" and data.get("rates", {}).get("TZS"):
            rate = float(data["rates"]["TZS"])
            _rate_cache["rate"] = rate
            _rate_cache["fetched_at"] = now
            logger.info(f"Live TZS/USD rate (primary): {rate}")
            return rate
    except Exception as exc:
        logger.warning(f"Primary rate API failed: {exc}")

    # Secondary API
    try:
        resp = requests.get(
            "https://api.exchangerate.host/latest?base=USD&symbols=TZS", timeout=5
        )
        data = resp.json()
        if data.get("rates", {}).get("TZS"):
            rate = float(data["rates"]["TZS"])
            _rate_cache["rate"] = rate
            _rate_cache["fetched_at"] = now
            logger.info(f"Live TZS/USD rate (secondary): {rate}")
            return rate
    except Exception as exc:
        logger.warning(f"Secondary rate API failed: {exc}")

    # Allow stale cache (rate was live at some point) — but only up to 10 minutes
    if _rate_cache["rate"] and (now - _rate_cache["fetched_at"]) < 600:
        logger.warning("Using stale cached TZS/USD rate (< 10 min old)")
        return _rate_cache["rate"]

    # No live rate, no recent cache — refuse to guess
    logger.error("All exchange rate APIs failed and no recent cache — refusing to convert")
    raise ExchangeRateUnavailable(
        "Unable to fetch a live exchange rate. Please try again in a moment or pay in TZS."
    )


def _normalize_phone(phone: str) -> str:
    """Normalize phone to international format without + (e.g. 255745636924).
    Handles: +255..., 0255..., 07..., 06..., etc."""
    phone = phone.strip().replace(" ", "").replace("-", "").replace("+", "")
    # Tanzania local numbers starting with 0
    if phone.startswith("0") and len(phone) >= 9:
        phone = "255" + phone[1:]
    # If still doesn't start with country code, assume Tanzania
    if not phone.startswith("255") and len(phone) <= 9:
        phone = "255" + phone
    return phone

# Cache token in memory (valid for 1 hour)
_token_cache = {"token": None, "expires": 0}


def _get_auth_token():
    """Get a JWT token from ClickPesa, with simple caching."""
    import time

    if _token_cache["token"] and time.time() < _token_cache["expires"]:
        return _token_cache["token"]

    url = f"{settings.CLICKPESA_API_URL}/third-parties/generate-token"
    headers = {
        "Content-Type": "application/json",
        "client-id": settings.CLICKPESA_CLIENT_ID,
        "api-key": settings.CLICKPESA_API_KEY,
    }

    response = requests.post(url, headers=headers, timeout=15)
    data = response.json()

    if data.get("success") and data.get("token"):
        _token_cache["token"] = data["token"]
        _token_cache["expires"] = time.time() + 3500  # ~58 minutes
        logger.info("ClickPesa auth token obtained")
        return data["token"]

    logger.error(f"ClickPesa auth failed: {data}")
    raise Exception(f"ClickPesa auth failed: {data.get('message', 'Unknown error')}")


def generate_checkout_link(
    amount: float,
    order_reference: str,
    currency: str = "TZS",
    customer_name: str = "",
    customer_email: str = "",
    customer_phone: str = "",
):
    """Generate a ClickPesa hosted checkout link."""
    token = _get_auth_token()

    url = f"{settings.CLICKPESA_API_URL}/third-parties/checkout-link/generate-checkout-url"
    headers = {
        "Content-Type": "application/json",
        "Authorization": token,
    }
    payload = {
        "totalPrice": str(int(amount)) if currency == "TZS" else str(round(amount, 2)),
        "orderReference": order_reference,
        "orderCurrency": currency,
        "customerName": customer_name,
        "customerEmail": customer_email,
        "customerPhone": _normalize_phone(customer_phone),
    }

    try:
        logger.info(f"ClickPesa checkout request: {order_reference} | {amount} {currency}")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        data = response.json()

        if response.status_code in (200, 201) and data.get("checkoutLink"):
            logger.info(f"ClickPesa checkout link: {data['checkoutLink']}")
            return {"success": True, "checkout_url": data["checkoutLink"]}

        logger.error(f"ClickPesa error {response.status_code}: {data}")
        return {"success": False, "error": data.get("message", str(data))}

    except Exception as e:
        logger.error(f"ClickPesa request failed: {e}")
        return {"success": False, "error": str(e)}
