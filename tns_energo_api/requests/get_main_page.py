from types import MappingProxyType
from typing import Any, Iterable, List, Mapping, Optional, TYPE_CHECKING, Tuple, Union

import attr

from tns_energo_api.converters import (
    DataMapping,
    META_SOURCE_DATA_KEY,
    RequestMapping,
    conv_bool,
    conv_float,
    conv_str_optional,
    conv_str_stripped,
    wrap_default_none,
)
from tns_energo_api.exceptions import EmptyResultException

if TYPE_CHECKING:
    from tns_energo_api import TNSEnergoAPI


@attr.s(kw_only=True, frozen=True, slots=True)
class EmailInvoiceStatus(DataMapping):
    code: str = attr.ib(
        converter=conv_str_stripped,
        metadata={META_SOURCE_DATA_KEY: "ls"},
    )
    email: Optional[str] = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "email"},
        default=None,
    )
    digital_invoices_email: Optional[str] = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "kvit_email"},
        default=None,
    )
    digital_invoices_enabled: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "kvit_enabled"},
        default=False,
    )
    digital_invoices_ignored: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "ignore_ekvit"},
        default=False,
    )
    digital_invoices_email_comment: Optional[str] = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "kvit_email_string"},
        default=None,
    )
    result: bool = attr.ib(converter=conv_bool, metadata={META_SOURCE_DATA_KEY: "result"})


@attr.s(kw_only=True, frozen=True, slots=True)
class TicketsInfo(DataMapping):
    resolved: int = attr.ib(
        converter=wrap_default_none(int, 0),
        metadata={META_SOURCE_DATA_KEY: "resolved"},
        default=0,
    )
    with_answer: int = attr.ib(
        converter=wrap_default_none(int, 0),
        metadata={META_SOURCE_DATA_KEY: "with_answer"},
    )


def _converter__banners(value: Iterable[Mapping[str, str]]) -> Tuple[Mapping[str, str], ...]:
    return tuple(map(MappingProxyType, value))


def _converter__email_invoice_status(value: Union[Mapping[str, Any], EmailInvoiceStatus]):
    if isinstance(value, EmailInvoiceStatus):
        return value
    return EmailInvoiceStatus.from_response(value)


def _converter__tickets_info(value: Union[Mapping[str, Any]]) -> TicketsInfo:
    if isinstance(value, TicketsInfo):
        return value
    return TicketsInfo.from_response(value)


@attr.s(kw_only=True, frozen=True, slots=True)
class GetMainPage(RequestMapping):
    @classmethod
    async def async_request_raw(cls, on: "TNSEnergoAPI", code: str):
        return await on.async_req_get(
            ("region", on.region, "action", "getMainpage", "ls", code, "json"),
        )

    @classmethod
    async def async_request(cls, on: "TNSEnergoAPI", code: str):
        result = await cls.async_request_raw(on, code)
        if result is None:
            raise EmptyResultException("Response result is empty")
        return cls.from_response(result)

    cost_of_restriction: float = attr.ib(
        converter=conv_float,
        default=0.0,
        metadata={META_SOURCE_DATA_KEY: "COST-OF-RESTRICTION"},
    )
    cost_of_resuming: float = attr.ib(
        converter=conv_float,
        default=0.0,
        metadata={META_SOURCE_DATA_KEY: "COST-OF-RESUMING"},
    )
    summ: float = attr.ib(
        converter=conv_float,
        metadata={META_SOURCE_DATA_KEY: "summ"},
    )
    email_invoice_status: "EmailInvoiceStatus" = attr.ib(
        converter=_converter__email_invoice_status,
        metadata={META_SOURCE_DATA_KEY: "emailAndKvitStatus"},
    )
    banners: List[Mapping[str, str]] = attr.ib(
        converter=_converter__banners,
        factory=tuple,
        metadata={META_SOURCE_DATA_KEY: "banners"},
    )
    notifications: List[Any] = attr.ib(
        converter=tuple,
        metadata={META_SOURCE_DATA_KEY: "notifications"},
    )
    tickets_info: "TicketsInfo" = attr.ib(
        converter=_converter__tickets_info,
        metadata={META_SOURCE_DATA_KEY: "ticketsInfo"},
    )
