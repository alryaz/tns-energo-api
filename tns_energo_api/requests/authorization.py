from typing import Any, Mapping, Optional, Sequence, TYPE_CHECKING, Union

import attr

from tns_energo_api.converters import (
    DataMapping,
    META_SOURCE_DATA_KEY,
    RequestMapping,
    conv_bool,
    conv_float,
    conv_str_optional,
    wrap_default_none,
)
from tns_energo_api.requests.account import AccountInfo, converter__ls_list

if TYPE_CHECKING:
    from tns_energo_api import TNSEnergoAPI


@attr.s(kw_only=True, frozen=True, slots=True)
class EmailAndKvitStatus(DataMapping):
    code: str = attr.ib(
        converter=str,
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
    result: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "result"},
    )


@attr.s(kw_only=True, frozen=True, slots=True)
class Consent(DataMapping):
    pd: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "pd"},
    )
    digital: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "digital"},
    )


def _converter__email_and_kvit_status(
    value: Union[Mapping[str, Any], EmailAndKvitStatus]
) -> EmailAndKvitStatus:
    if isinstance(value, EmailAndKvitStatus):
        return value
    return EmailAndKvitStatus.from_response(value)


def _converter__consent(value: Union[Consent, Mapping[str, Any]]) -> Consent:
    return value if isinstance(value, Consent) else Consent.from_response(value)


@attr.s(kw_only=True, frozen=True, slots=True)
class AuthorizationRequest(RequestMapping):
    @classmethod
    async def async_request_raw(cls, on: "TNSEnergoAPI", username: str, password: str):
        return await on.async_req_post(
            ("region", on.region, "action", "authorization", "json"),
            {"ls": username, "password": password},
        )

    @classmethod
    async def async_request(cls, on: "TNSEnergoAPI", username: str, password: str):
        return cls.from_response(await cls.async_request_raw(on, username, password))

    # Required attributes
    code: str = attr.ib(
        converter=str,
        metadata={META_SOURCE_DATA_KEY: "LS"},
    )
    is_controlled: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "IS_SLAVE"},
        default=False,
    )
    controlled_by_code: Optional[str] = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "MASTER_LS"},
        default=None,
    )
    is_controlling: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "IS_MASTER"},
        default=False,
    )
    email: Optional[str] = attr.ib(
        converter=str,
        metadata={META_SOURCE_DATA_KEY: "EMAIL"},
        default=None,
    )
    digital_invoices_ignored: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "ignore_ekvit"},
        default=False,
    )
    _email_and_invoice_status: EmailAndKvitStatus = attr.ib(
        converter=_converter__email_and_kvit_status,
        metadata={META_SOURCE_DATA_KEY: "emailAndKvitStatus"},
    )
    address: Optional[str] = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "ADDRESS"},
        default=None,
    )
    debt: float = attr.ib(
        converter=wrap_default_none(float, 0.0),
        metadata={META_SOURCE_DATA_KEY: "BALANCE"},
        default=0.0,
    )

    @property
    def balance(self) -> float:
        return -self.debt

    @property
    def digital_invoices_email(self) -> str:
        return self._email_and_invoice_status.digital_invoices_email

    @property
    def digital_invoices_enabled(self) -> bool:
        return self._email_and_invoice_status.digital_invoices_enabled

    @property
    def digital_invoices_email_comment(self) -> str:
        return self._email_and_invoice_status.digital_invoices_email_comment

    # Optional attributes
    dependent_accounts: Sequence[AccountInfo] = attr.ib(
        converter=converter__ls_list,
        metadata={META_SOURCE_DATA_KEY: "SLAVE_LS_LIST"},
        default=(),
    )
    has_account_without_invoices: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "has_ls_without_kvit"},
    )
    consent: Consent = attr.ib(
        converter=_converter__consent,
        metadata={META_SOURCE_DATA_KEY: "CONSENT"},
    )
    password_hash: str = attr.ib(
        converter=str,
        metadata={META_SOURCE_DATA_KEY: "PWD"},
    )
    status: str = attr.ib(
        converter=str,
        metadata={META_SOURCE_DATA_KEY: "STATUS"},
    )
    check_email_kvt_param: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "checkEmailKvtParam"},
    )
    company_name: str = attr.ib(
        converter=str,
        metadata={META_SOURCE_DATA_KEY: "COMPANY_NAME"},
    )
    is_allow_delegation: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "IS_ALLOW_DELEGATION"},
    )
