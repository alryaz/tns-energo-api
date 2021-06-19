from typing import Any, Iterable, List, Mapping, Optional, Sequence, TYPE_CHECKING, Tuple, Union

import attr

from tns_energo_api.converters import (
    DataMapping,
    META_SOURCE_DATA_KEY,
    RequestMapping,
    conv_bool,
    conv_int,
    conv_str_optional,
    wrap_default_none,
)
from tns_energo_api.exceptions import ResponseException

if TYPE_CHECKING:
    from tns_energo_api import TNSEnergoAPI


#################################################################################
# Account info
#################################################################################


@attr.s(kw_only=True, frozen=True, slots=True)
class AccountInfo(DataMapping):
    # Required attributes
    address: str = attr.ib(
        converter=str,
        metadata={META_SOURCE_DATA_KEY: "cache_address"},
    )
    debt: float = attr.ib(
        converter=wrap_default_none(float, 0.0),
        metadata={META_SOURCE_DATA_KEY: "cache_balance"},
    )
    code: Optional[str] = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "ls"},
        default=None,
    )
    email: Optional[str] = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "email"},
    )
    digital_invoices_ignored: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "ignore_ekvit"},
    )
    digital_invoices_email: Optional[str] = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "kvit_email"},
    )
    digital_invoices_enabled: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "kvit_enabled"},
    )
    digital_invoices_email_comment: str = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "kvit_email_string"},
        default=None,
    )
    is_controlled: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "is_slave_ls"},
    )
    is_controlling: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "is_master_ls"},
    )
    controlled_by_code: str = attr.ib(
        converter=str,
        metadata={META_SOURCE_DATA_KEY: "master_ls"},
    )

    # Optional attributes
    alias: str = attr.ib(
        converter=str,
        metadata={META_SOURCE_DATA_KEY: "alias"},
    )
    controlling_code: str = attr.ib(
        converter=str,
        metadata={META_SOURCE_DATA_KEY: "slave_ls"},
    )
    is_locked: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "is_locked"},
    )
    avatar_type: int = attr.ib(
        converter=conv_int,
        metadata={META_SOURCE_DATA_KEY: "avatar_type"},
    )

    @property
    def balance(self) -> float:
        return -self.debt


def converter__ls_list(
    value: Iterable[Union[Mapping[str, Any], AccountInfo]],
) -> Tuple[AccountInfo, ...]:
    return tuple(
        subvalue if isinstance(subvalue, AccountInfo) else AccountInfo.from_response(subvalue)
        for subvalue in value
    )


@attr.s(kw_only=True, frozen=True, slots=True)
class MeterDescription(DataMapping):
    install_location: str = attr.ib(
        converter=str,
        metadata={META_SOURCE_DATA_KEY: "MestoUst"},
    )
    status: str = attr.ib(
        converter=str,
        metadata={META_SOURCE_DATA_KEY: "RaschSch"},
    )
    code: str = attr.ib(
        converter=str,
        metadata={META_SOURCE_DATA_KEY: "ZavodNomer"},
    )


def _converter__counters(
    value: Iterable[Union[Mapping[str, Any], MeterDescription]]
) -> Tuple[MeterDescription, ...]:
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
        return cls.from_response(await cls.async_request_raw(on, code))

    address: str = attr.ib(
        converter=str,
        metadata={META_SOURCE_DATA_KEY: "ADDRESS"},
    )
    contact: str = attr.ib(
        converter=str,
        metadata={META_SOURCE_DATA_KEY: "TELNANIMATEL"},
    )
    people_registered: int = attr.ib(
        converter=int,
        metadata={META_SOURCE_DATA_KEY: "CHISLOPROPISAN"},
    )
    total_area: float = attr.ib(
        converter=float,
        metadata={META_SOURCE_DATA_KEY: "OBSCHPLOSCHAD"},
    )
    living_area: int = attr.ib(
        converter=int,
        metadata={META_SOURCE_DATA_KEY: "JILPLOSCHAD"},
    )
    ownership_document: str = attr.ib(
        converter=str,
        metadata={META_SOURCE_DATA_KEY: "DOCSOBSTV"},
    )
    living_category: str = attr.ib(
        converter=str,
        metadata={META_SOURCE_DATA_KEY: "KATEGJIL"},
    )
    sn_koefsezon: int = attr.ib(
        converter=int,
        metadata={META_SOURCE_DATA_KEY: "SN_KOEFSEZON"},
    )
    sn_objem: int = attr.ib(
        converter=int,
        metadata={META_SOURCE_DATA_KEY: "SN_OBJEM"},
    )
    invoice_is_digital: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "DIGITAL_RECEIPT"},
    )
    meters: List["MeterDescription"] = attr.ib(
        converter=_converter__counters,
        metadata={META_SOURCE_DATA_KEY: "counters"},
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
        return cls.from_response(await cls.async_request_raw(on, code, dlogin))

    data: Sequence[AccountInfo] = attr.ib(
        converter=converter__ls_list,
        metadata={META_SOURCE_DATA_KEY: "data"},
    )
    email: str = attr.ib(
        converter=str,
        metadata={META_SOURCE_DATA_KEY: "email"},
    )
    is_controlled: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "is_slave"},
    )
    is_controlling: bool = attr.ib(
        converter=bool,
        metadata={META_SOURCE_DATA_KEY: "is_master"},
    )
    digital_invoices_enabled: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "kvit_enabled"},
    )
    has_account_without_invoices: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "has_ls_without_kvit"},
    )
