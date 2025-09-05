"""
Model representing a currency amount (to a maximum of two decimal places) with its ISO 4217 code.
"""

from decimal import (
    Decimal,
)
from typing import (
    Any,
    Union,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    PastDate,
    model_validator,
)
from pydantic_extra_types.currency_code import (
    ISO4217,
)

from ..data import (
    ABBREVIATIONS,
    CURRENCY_SYMBOL_TO_CODE_MAP,
)
from ..extra_types import (
    Number,
    FxProviderStr,
)
from ..services import (
    convert,
)


class Currency(BaseModel):
    """
    Model representing a currency amount (to a maximum of
    two decimal places) with its ISO 4217 code.

    Args:
        value (Number): Decimal value of the amount, max two decimal places.
        code (Union[ISO4217, None], optional): ISO 4217 currency code. Defaults to None.

    Returns:
        Currency: An instance of the Currency model.

    Examples:
        >>> from pycountant.models import Currency
        >>> amount = Currency(value="$12.34k")
        >>> print(amount)
        12,340.00 USD
        >>> from datetime import date
        >>> converted_amount = amount.convert(to="EUR", on=date(2023, 1, 5))
        >>> print(converted_amount)
        11,640.41 EUR

    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )
    value: Number
    code: Union[ISO4217, None] = None

    def __str__(self) -> str:
        return f"{self.value:,} {self.code}"

    def convert(
        self,
        *,
        to: ISO4217,
        on: PastDate,
        using: FxProviderStr = "European Central Bank",
    ) -> "Currency":
        """
        Convert the value to its value in another currency
        using a specified FX provider and date.

        Args:
            to (ISO4217): The ISO 4217 currency code to convert to.
            on (PastDate): The date to use for the conversion rate
                           (cannot be in the future).
            using (FxProviderStr, optional): The fx provider to
                                             convert with.
                                             Defaults to
                                             "European Central Bank".

        Returns:
            Currency: The converted Currency.
        """
        converted = convert(value=self.value, of=self.code, to=to, on=on, using=using)
        return self.__class__(value=converted, code=to)

    @classmethod
    def decountify(cls, value: str) -> Union[Decimal, str]:
        """
        Negative numbers are sometimes represented by accountants
        between brackets.
        Therefore remove these and prefix with "-".

        If abbreviations are used (e.g. "k" for a thousand),
        convert the value as appropriate.


        Args:
            value (str): The number str.

        Returns:
            Union[Decimal, str]: The number str decountified.
        """
        # Handle negative values in parentheses and remove commas
        value = value.replace("(", "-").replace(")", "").replace(",", "")
        # Handle abbreviations like k (e.g. 1.2k = 1200)
        final_char = value[-1]
        if final_char in ABBREVIATIONS:
            return Decimal(value[:-1]) * ABBREVIATIONS[final_char]
        return value

    @model_validator(mode="before")
    @classmethod
    def parse_data(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        Infers currency code if information provided in value.

        Args:
            data (dict[str, Any]): Data passed before validation.

        Returns:
            dict[str, Any]: Cleaned data before validation.
        """
        value = data.get("value")
        code = data.get("code")
        # Handle case where, for example, pass "£" instead of "GBP" for code.
        if code and code not in ISO4217.allowed_currencies and isinstance(code, str):
            code = code.strip()
            if code := CURRENCY_SYMBOL_TO_CODE_MAP.get(code):
                data["code"] = code
        # Handle case where value is a string with currency symbol (e.g. "£1234")
        if value and isinstance(value, str):
            value = value.strip()
            symbols = [
                symbol for symbol in CURRENCY_SYMBOL_TO_CODE_MAP if symbol in value
            ]
            if symbols and len(symbols) == 1:
                # Remove the symbol from the value
                symbol = symbols[0]
                value = value.replace(symbol, "")
                # Only set the code if it wasn't already provided
                # (for example, to prevent CAD being overwritten by USD)
                if not code:
                    data["code"] = CURRENCY_SYMBOL_TO_CODE_MAP[symbol]
            # Handle negatives presented as (1,000), for example, and remove commas
            value = cls.decountify(value=value)
            data["value"] = value
        return data


if __name__ == "__main__":
    import doctest

    doctest.testmod()
