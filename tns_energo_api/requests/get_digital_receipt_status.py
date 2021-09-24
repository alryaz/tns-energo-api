from datetime import date
from typing import Optional, TYPE_CHECKING

import attr

from tns_energo_api.converters import (
    META_SOURCE_DATA_KEY,
    RequestMapping,
    conv_bool,
    conv_date_optional,
    conv_str_optional,
)
from tns_energo_api.exceptions import EmptyResultException

if TYPE_CHECKING:
    from tns_energo_api import TNSEnergoAPI


@attr.s(kw_only=True, frozen=True, slots=True)
class GetDigitalReceiptStatus(RequestMapping):
    @classmethod
    async def async_request_raw(cls, on: "TNSEnergoAPI", code: str):
        return await on.async_req_get(
            ("region", on.region, "action", "getDigitalReceiptStatus", "ls", code, "json")
        )

    @classmethod
    async def async_request(cls, on: "TNSEnergoAPI", code: str):
        result = await cls.async_request_raw(on, code)
        if result is None:
            raise EmptyResultException("Response result is empty")
        return cls.from_response(result)

    send_invoices: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "sendKvt"},
        default=False,
    )
    email_verification_required: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "EMAILVERIFY"},
        default=False,
    )
    profile_email: Optional[str] = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "registeredEmail"},
        default=None,
    )
    invoices_email: Optional[str] = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "sendKvtEmail"},
        default=None,
    )
    active_since: Optional[date] = attr.ib(
        converter=conv_date_optional,
        metadata={META_SOURCE_DATA_KEY: "sendKvtEmailFrom"},
        default=None,
    )
    active_until: Optional[date] = attr.ib(
        converter=conv_date_optional,
        metadata={META_SOURCE_DATA_KEY: "sendKvtEmailTo"},
        default=None,
    )
