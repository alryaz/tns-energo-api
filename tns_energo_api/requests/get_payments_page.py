from datetime import date as date_sys, datetime as datetime_sys
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Optional, Sequence, TYPE_CHECKING, Tuple, Union

import attr

from tns_energo_api.converters import (
    DataMapping,
    META_SOURCE_DATA_KEY,
    RequestMapping,
    conv_bool,
    conv_date,
    conv_datetime,
    conv_str_stripped,
    wrap_default_none,
    wrap_optional_eval,
    wrap_optional_none,
    wrap_str_stripped,
)

if TYPE_CHECKING:
    from tns_energo_api import TNSEnergoAPI


@attr.s(kw_only=True, frozen=True, slots=True)
class PaymentData(DataMapping):
    date: date_sys = attr.ib(
        converter=conv_date,
        metadata={META_SOURCE_DATA_KEY: "DATE"},
    )
    datetime: Optional[datetime_sys] = attr.ib(
        converter=wrap_optional_none(wrap_str_stripped(wrap_optional_eval(conv_datetime))),
        metadata={META_SOURCE_DATA_KEY: "DATETIME"},
    )
    source: Optional[str] = attr.ib(
        converter=wrap_optional_none(conv_str_stripped),
        metadata={META_SOURCE_DATA_KEY: "ISTOCHNIK"},
        default=None,
    )
    amount: float = attr.ib(
        converter=wrap_default_none(float, 0.0),
        metadata={META_SOURCE_DATA_KEY: "SUMMA"},
        default=0.0,
    )
    transaction_id: Optional[str] = attr.ib(
        converter=wrap_optional_none(wrap_str_stripped(wrap_optional_eval(str))),
        metadata={META_SOURCE_DATA_KEY: "TRANSACTION"},
        default=None,
    )


def converter__history(
    value: Union[
        Mapping[Union[str, int], Iterable[Union[Mapping[str, Any], PaymentData]]], Iterable
    ],
) -> Mapping[str, Tuple[PaymentData, ...]]:
    if not isinstance(value, Mapping):
        if not value:
            return {}
        raise TypeError("invalid mapping")

    return MappingProxyType(
        {
            year: tuple(
                sorted(
                    (
                        (
                            payment_data
                            if isinstance(payment_data, PaymentData)
                            else PaymentData.from_response(payment_data)
                        )
                        for payment_data in payment_data_list
                    ),
                    key=lambda x: (x.date, x.datetime or 0),
                )
            )
            for year, payment_data_list in value.items()
        }
    )


@attr.s(kw_only=True, frozen=True, slots=True)
class GetPaymentsPage(RequestMapping):
    @classmethod
    async def async_request_raw(cls, on: "TNSEnergoAPI", code: str):
        return await on.async_req_get(
            ("region", on.region, "action", "getPaymentsHistPage", "ls", code, "json"),
        )

    @classmethod
    async def async_request(cls, on: "TNSEnergoAPI", code: str):
        return cls.from_response(await cls.async_request_raw(on, code))

    result: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "result"},
    )
    history: Mapping[str, Sequence[PaymentData]] = attr.ib(
        converter=converter__history,
        metadata={META_SOURCE_DATA_KEY: "history"},
    )
