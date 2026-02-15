from datetime import datetime

# Add Indian market holidays manually (example 2026)
MARKET_HOLIDAYS = {
    "2026-01-26",
    "2026-03-29",
    "2026-08-15",
    "2026-10-02"
}

def market_is_open():
    now = datetime.now()

    today_str = now.strftime("%Y-%m-%d")

    # Weekend
    if now.weekday() > 4:
        return False

    # Holiday
    if today_str in MARKET_HOLIDAYS:
        return False

    # Market hours 9:30–15:30 IST
    if now.hour < 9 or now.hour > 15:
        return False

    if now.hour == 9 and now.minute < 30:
        return False

    if now.hour == 15 and now.minute > 30:
        return False

    return True
