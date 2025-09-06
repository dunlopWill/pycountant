"""
Data related to currency including common
abbreviations and maps of symbols to codes.
"""

from pydantic_extra_types.currency_code import (
    ISO4217,
)


CURRENCY_SYMBOL_TO_CODE_MAP: dict[str, ISO4217] = {
    "$": ISO4217("USD"),
    "£": ISO4217("GBP"),
    "€": ISO4217("EUR"),
    "¥": ISO4217("JPY"),
    "₹": ISO4217("INR"),
    "₽": ISO4217("RUB"),
}

ABBREVIATIONS: dict[str, int] = {
    "k": 1_000,
    "m": 1_000_000,
    "b": 1_000_000_000,
    "t": 1_000_000_000_000,
}
