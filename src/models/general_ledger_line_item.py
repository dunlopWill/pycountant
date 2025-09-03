from datetime import (
    date,
    datetime,
)
from decimal import (
    Decimal,
)
from typing import (
    Any,
    Literal,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    computed_field,
    field_validator,
)

from .currency import (
    Currency,
)


class GeneralLedgerLineItem(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        coerce_numbers_to_str=True,
    )
    account_code: str
    journal_number: str
    net: Currency
    effective: date
    created: datetime
    user: str
    reference: str
    line_description: str
    journal_description: str

    @computed_field
    @property
    def abs(self) -> Currency:
        return Currency(value=abs(self.net.value))

    @computed_field
    @property
    def position(self) -> Literal["debit", "credit"]:
        return "debit" if self.net.value >= 0 else "credit"

    @field_validator("net", mode="before")
    @classmethod
    def parse_net(cls, value: Any) -> Any:
        if isinstance(value, (int, float, Decimal, str)):
            return Currency(value=value)
        return value
