from decimal import (
    Decimal,
)
from typing import (
    Any,
    Union,
    cast,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PastDate,
    model_validator,
)
from pydantic.fields import (
    ModelPrivateAttr,
)
from pydantic_extra_types.currency_code import (
    ISO4217,
)

from ..extra_types import (
    Number,
    ProviderStr,
)
from ..services import (
    convert,
)


class Currency(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )
    value: Number
    code: Union[ISO4217, None] = Field(init=False, default=None)

    _code_map: dict[str, ISO4217] = {
        "$": "USD",
        "£": "GBP",
        "€": "EUR",
        "¥": "JPY",
        "₹": "INR",
        "₽": "RUB",
    }

    def __str__(self) -> str:
        return f"{self.value:,} {self.code}"

    def convert(self, *, to: ISO4217, on: PastDate, using: ProviderStr) -> "Currency":
        converted = convert(value=self.value, of=self.code, to=to, on=on, using=using)
        return self.__class__(value=converted, code=to)

    @model_validator(mode="before")
    @classmethod
    def check_for_currency_symbol(cls, data: Any) -> Any:
        _code_map = cast(ModelPrivateAttr, cls._code_map)
        code_map = _code_map.default
        if isinstance(data, dict):
            if code := data.get("code"):
                if code in code_map:
                    data["code"] = code_map[code]
                    return data
            if value := data.get("value"):
                if isinstance(value, str):
                    for symbol, code in code_map.items():
                        if symbol in value:
                            # Only set the code if it wasn't already provided
                            # This can prevent CAD being overwritten by USD
                            if not data.get("code"):
                                data["code"] = code
                            value = value.replace(symbol, "")
                            break
                    # Handle negative values in parentheses and remove commas
                    value = (
                        value.replace("(", "-")
                        .replace(")", "")
                        .replace(",", "")
                        .strip()
                    )
                    if value.endswith("k"):
                        value = Decimal(value[:-1]) * 1_000
                    elif value.endswith("m"):
                        value = Decimal(value[:-1]) * 1_000_000
                    elif value.endswith("b"):
                        value = Decimal(value[:-1]) * 1_000_000_000
                    data["value"] = value
        return data
