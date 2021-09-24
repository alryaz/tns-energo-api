from typing import Any, Iterable, Mapping, Optional, Sequence, TYPE_CHECKING, Tuple, Union

import attr

from tns_energo_api.converters import (
    DataMapping,
    META_SOURCE_DATA_KEY,
    RequestMapping,
    conv_bool,
    conv_int,
    conv_str_optional,
    conv_str_stripped,
    wrap_default_none,
    wrap_optional_none,
)
from tns_energo_api.exceptions import EmptyResultException

if TYPE_CHECKING:
    from tns_energo_api import TNSEnergoAPI


#################################################################################
# Account info
#################################################################################


@attr.s(kw_only=True, frozen=True, slots=True)
class AccountInfo(DataMapping):
    address: str = attr.ib(
        converter=wrap_default_none(str, ""),
        metadata={META_SOURCE_DATA_KEY: "cache_address"},
        default="",
    )
    debt: float = attr.ib(
        converter=wrap_default_none(float, 0.0),
        metadata={META_SOURCE_DATA_KEY: "cache_balance"},
        default=None,
    )
    code: Optional[str] = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "ls"},
        default=None,
    )
    email: Optional[str] = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "email"},
        default=None,
    )
    digital_invoices_ignored: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "ignore_ekvit"},
        default=False,
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
    digital_invoices_email_comment: str = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "kvit_email_string"},
        default=None,
    )
    is_controlled: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "is_slave_ls"},
        default=False,
    )
    is_controlling: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "is_master_ls"},
        default=False,
    )
    controlled_by_code: Optional[str] = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "master_ls"},
        default=None,
    )
    alias: Optional[str] = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "alias"},
        default=None,
    )
    controlling_code: Optional[str] = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "slave_ls"},
        default=None,
    )
    is_locked: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "is_locked"},
        default=False,
    )
    avatar_type: int = attr.ib(
        converter=conv_int,
        metadata={META_SOURCE_DATA_KEY: "avatar_type"},
        default=0,
    )

    @property
    def balance(self) -> float:
        return -self.debt


def converter__ls_list(
    value: Optional[Iterable[Union[Mapping[str, Any], AccountInfo]]],
) -> Tuple[AccountInfo, ...]:
    if value is None:
        return ()
    return tuple(
        subvalue if isinstance(subvalue, AccountInfo) else AccountInfo.from_response(subvalue)
        for subvalue in value
    )


@attr.s(kw_only=True, frozen=True, slots=True)
class MeterDescription(DataMapping):
    install_location: str = attr.ib(
        converter=conv_str_stripped,
        metadata={META_SOURCE_DATA_KEY: "MestoUst"},
    )
    status: str = attr.ib(
        converter=conv_str_stripped,
        metadata={META_SOURCE_DATA_KEY: "RaschSch"},
    )
    code: str = attr.ib(
        converter=conv_str_stripped,
        metadata={META_SOURCE_DATA_KEY: "ZavodNomer"},
    )


def _converter__counters(
    value: Optional[Iterable[Union[Mapping[str, Any], MeterDescription]]]
) -> Tuple[MeterDescription, ...]:
    if value is None:
        return ()
    return tuple(
        subvalue
        if isinstance(subvalue, MeterDescription)
        else MeterDescription.from_response(subvalue)
        for subvalue in value
    )


@attr.s(kw_only=True, frozen=True, slots=True)
class GetInfo(RequestMapping):
    @classmethod
    async def async_request_raw(cls, on: "TNSEnergoAPI", code: str) -> Mapping[str, Any]:
        return await on.async_req_get(
            ("region", on.region, "action", "getInfo", "ls", code + "asdf", "json"),
        )

    @classmethod
    async def async_request(cls, on: "TNSEnergoAPI", code: str):
        result = await cls.async_request_raw(on, code)
        if result is None:
            raise EmptyResultException("Response result is empty")
        return cls.from_response(result)

    address: str = attr.ib(
        converter=wrap_default_none(str, ""),
        metadata={META_SOURCE_DATA_KEY: "ADDRESS"},
        default="",
    )
    contact: Optional[str] = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "TELNANIMATEL"},
        default=None,
    )
    people_registered: Optional[int] = attr.ib(
        converter=wrap_optional_none(int),
        metadata={META_SOURCE_DATA_KEY: "CHISLOPROPISAN"},
        default=None,
    )
    total_area: Optional[float] = attr.ib(
        converter=wrap_default_none(float, None),
        metadata={META_SOURCE_DATA_KEY: "OBSCHPLOSCHAD"},
        default=None,
    )
    living_area: Optional[int] = attr.ib(
        converter=wrap_optional_none(int),
        metadata={META_SOURCE_DATA_KEY: "JILPLOSCHAD"},
        default=None,
    )
    ownership_document: Optional[str] = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "DOCSOBSTV"},
        default=None,
    )
    living_category: str = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "KATEGJIL"},
        default=None,
    )
    seasonal_coefficient: Optional[int] = attr.ib(
        converter=wrap_optional_none(int),
        metadata={META_SOURCE_DATA_KEY: "SN_KOEFSEZON"},
        default=None,
    )
    volume: Optional[int] = attr.ib(
        converter=wrap_optional_none(int),
        metadata={META_SOURCE_DATA_KEY: "SN_OBJEM"},
        default=None,
    )
    invoice_is_digital: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "DIGITAL_RECEIPT"},
        default=False,
    )
    meters: Tuple["MeterDescription", ...] = attr.ib(
        converter=_converter__counters,
        metadata={META_SOURCE_DATA_KEY: "counters"},
        default=(),
    )


#################################################################################
# Account list
#################################################################################


@attr.s(kw_only=True, frozen=True, slots=True)
class GetLSListByLS(RequestMapping):
    @classmethod
    async def async_request_raw(cls, on: "TNSEnergoAPI", code: str, dlogin: int = 0):
        return await on.async_req_post(
            ("delegation", "getLSListByLs", code),
            {"for_ls": code, "dlogin": dlogin},
        )

    @classmethod
    async def async_request(cls, on: "TNSEnergoAPI", code: str, dlogin: int = 0):
        response = await cls.async_request_raw(on, code, dlogin)
        if response is None:
            raise EmptyResultException("Response result is empty")
        return cls.from_response(response)

    data: Sequence[AccountInfo] = attr.ib(
        converter=converter__ls_list,
        metadata={META_SOURCE_DATA_KEY: "data"},
        default=(),
    )
    email: Optional[str] = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "email"},
        default=None,
    )
    is_controlled: bool = attr.ib(
        converter=wrap_default_none(conv_bool, False),
        metadata={META_SOURCE_DATA_KEY: "is_slave"},
        default=False,
    )
    is_controlling: bool = attr.ib(
        converter=wrap_default_none(conv_bool, False),
        metadata={META_SOURCE_DATA_KEY: "is_master"},
        default=False,
    )
    digital_invoices_enabled: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "kvit_enabled"},
        default=False,
    )
    has_account_without_invoices: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "has_ls_without_kvit"},
        default=False,
    )
