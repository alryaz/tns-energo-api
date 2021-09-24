__all__ = (
    "TNSEnergoAPI",
    "AccountCode",
    "Account",
    "Meter",
    "MeterZone",
    "Payment",
    "Indication",
    "NewIndication",
    "process_start_end_arguments",
    "converters",
    "exceptions",
    "requests",
)

import asyncio
import json
import logging
import uuid
from datetime import date, datetime
from io import StringIO
from types import MappingProxyType
from typing import (
    Any,
    ClassVar,
    Final,
    Iterable,
    List,
    Mapping,
    Optional,
    SupportsFloat,
    SupportsInt,
    Union,
)

import aiohttp
import attr
from multidict import MultiDict

from tns_energo_api.converters import DataMapping
from tns_energo_api.exceptions import (
    RequestException,
    RequestTimeoutException,
    ResponseException,
    TNSEnergoException,
)
from tns_energo_api.requests.account import GetInfo, GetLSListByLS
from tns_energo_api.requests.authorization import AuthorizationRequest
from tns_energo_api.requests.get_payments_page import GetPaymentsPage
from tns_energo_api.requests.get_readings_hist_page import GetReadingsHistPage
from tns_energo_api.requests.get_send_indications_page import SendIndicationsPage
from tns_energo_api.requests.send_readings import NewIndication, SendIndications

PathType = Union[str, Iterable[str]]
AccountCode = str


_LOGGER = logging.getLogger(__name__)


class TESTWRITER:
    def __init__(self) -> None:
        self._contents = StringIO()

    def __str__(self) -> str:
        return self._contents.getvalue()

    async def write(self, data):
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        self._contents.write(data)


def process_start_end_arguments(start: Optional[datetime], end: Optional[datetime]):
    if start is None:
        start = datetime.min
    elif isinstance(start, date):
        start = datetime.fromordinal(start.toordinal())

    if end is None:
        end = datetime.now()
    elif isinstance(end, date):
        end = datetime.fromordinal(end.toordinal())

    if start > end:
        raise ValueError("start cannot be greater than end")

    return start, end


# This is a lot, but having a timeout like this prevents multiple issues
DEFAULT_TIMEOUT: Final = aiohttp.ClientTimeout(total=30)


class TNSEnergoAPI:
    GLOBAL_APP_VERSION: ClassVar[str] = "1.60"
    GLOBAL_HASH: ClassVar[str] = "958fdc9525875bb8ef89e5c0bda3ebc60b95040e"

    REGIONS_MAP: ClassVar[Mapping[str, str]] = {
        "58": "penza",
        "76": "yar",
        "36": "voronezh",
        "53": "novgorod",
        "10": "karelia",
        "23": "kuban",
        "93": "kuban",
        "12": "mari-el",
        "52": "nn",
        "71": "tula",
        "61": "rostov",
    }

    @property
    def lk_region_url(self) -> str:
        return f"https://lk.{self.region}.tns-e.ru"

    def __init__(
        self,
        username: str,
        password: str,
        use_hash: Optional[str] = None,
        app_version: Optional[str] = None,
        timeout: Union[SupportsInt, SupportsFloat, aiohttp.ClientTimeout] = DEFAULT_TIMEOUT,
    ) -> None:
        try:
            self._region = self.REGIONS_MAP[username[:2]]
        except KeyError:
            raise ValueError("username does not match known regions")

        if not isinstance(timeout, aiohttp.ClientTimeout):
            if isinstance(timeout, SupportsInt):
                timeout = aiohttp.ClientTimeout(total=int(timeout))
            elif isinstance(timeout, SupportsFloat):
                timeout = aiohttp.ClientTimeout(total=float(timeout))
            else:
                raise TypeError("invalid argument type for timeout provided")

        self._username = username
        self._password = password
        self._local_hash = use_hash
        self._app_version = app_version
        self._session = aiohttp.ClientSession(
            timeout=timeout,
            cookie_jar=aiohttp.CookieJar(),
            headers={aiohttp.hdrs.USER_AGENT: "okhttp/3.7.0"},
        )

        self._main_account: Optional[Account] = None
        self._dependent_accounts: Optional[List[Account]] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self._session.__aexit__(*args)
        await self.async_close()

    async def async_close(self):
        if not self._session.closed:
            await self._session.close()

    @property
    def region(self) -> str:
        return self._region

    @property
    def username(self) -> str:
        return self._username

    @property
    def local_hash(self) -> str:
        return self._local_hash or self.GLOBAL_HASH

    @local_hash.setter
    def local_hash(self, value: Optional[str]) -> None:
        self._local_hash = value

    @property
    def local_app_version(self) -> str:
        return self._app_version or self.GLOBAL_APP_VERSION

    @local_app_version.setter
    def local_app_version(self, value: Optional[str]) -> None:
        self._app_version = value

    @property
    def requests_url_base(self) -> str:
        return f"https://rest.tns-e.ru/version/{self.local_app_version}/Android/mobile"

    async def async_req_get(self, path: Union[str, Iterable[str]]):
        if isinstance(path, str):
            target_url = path
        else:
            target_url = self.requests_url_base + "/" + "/".join(map(str, path)) + "/"

        try:
            _LOGGER.debug(f"[GET] -> ({target_url})")
            async with self._session.get(
                target_url,
                params={"hash": self.local_hash},
                raise_for_status=True,
            ) as response:
                response_status = response.status
                response_text = await response.text()

            try:
                response_json = json.loads(response_text)
            except json.JSONDecodeError as e:
                _LOGGER.error(f"[GET] <- [{response_status}] ({target_url}) {response_text}")
                raise ResponseException("Could not decode response data: %s" % repr(e))
            else:
                _LOGGER.debug(f"[GET] <- [{response_status}] ({target_url}) {response_json}")
                return response_json

        except aiohttp.ClientError as e:
            raise TNSEnergoException(
                "During request handling the following error occurred: %s" % repr(e)
            )

        except asyncio.TimeoutError:
            raise TNSEnergoException("During request handling a timeout occurred")

    async def async_req_post(self, path: Union[str, Iterable[str]], data: Any, name: str = "data"):
        with aiohttp.MultipartWriter(
            "multipart/form-data", boundary=str(uuid.uuid1())
        ) as mpdwriter:
            mpdwriter.append(
                json.dumps(data).replace(" ", ""),
                MultiDict(
                    {
                        aiohttp.hdrs.CONTENT_DISPOSITION: f'form-data; name="{name}"',
                        aiohttp.hdrs.CONTENT_TRANSFER_ENCODING: "binary",
                        aiohttp.hdrs.CONTENT_TYPE: "multipart/form-data; charset=utf-8",
                    }
                ),
            )
            if isinstance(path, str):
                target_url = path
            else:
                target_url = self.requests_url_base + "/" + "/".join(map(str, path)) + "/"

            try:
                _LOGGER.debug(f"[POST] -> ({target_url}) {data}")
                async with self._session.post(
                    target_url,
                    data=mpdwriter,
                    params={"hash": self.local_hash},
                    headers={
                        aiohttp.hdrs.CONTENT_TYPE: (
                            f"multipart/form-data; boundary={mpdwriter.boundary}"
                        ),
                        aiohttp.hdrs.CONNECTION: aiohttp.hdrs.KEEP_ALIVE,
                    },
                    raise_for_status=True,
                ) as response:
                    response_status = response.status
                    response_text = await response.text()

                try:
                    response_json = json.loads(response_text)
                except json.JSONDecodeError as e:
                    _LOGGER.error(
                        f"[POST] <- [{response_status}] ({target_url}) !NONJSON {response_text}"
                    )
                    raise ResponseException("Could not decode response data: %s" % repr(e))
                else:
                    _LOGGER.debug(f"[POST] <- [{response_status}] ({target_url}) {response_json}")
                    return response_json

            except aiohttp.ClientError as e:
                raise RequestException(
                    "During request handling the following error occurred: %s" % repr(e)
                )

            except asyncio.TimeoutError:
                raise RequestTimeoutException("During request handling a timeout occurred")

    def _make_account_from_response(self, response):
        return Account(
            api=self,
            address=response.address,
            debt=response.debt,
            code=response.code or response.controlling_code,
            email=response.email,
            digital_invoices_ignored=response.digital_invoices_ignored,
            digital_invoices_email=response.digital_invoices_email,
            digital_invoices_enabled=response.digital_invoices_enabled,
            digital_invoices_email_comment=response.digital_invoices_email_comment,
            is_controlled=response.is_controlled,
            is_controlling=response.is_controlling,
            controlled_by_code=response.controlled_by_code,
        )

    async def async_authenticate(self):
        response = await AuthorizationRequest.async_request(self, self._username, self._password)

        main_account = self._make_account_from_response(response)
        dependent_accounts = list(
            map(self._make_account_from_response, response.dependent_accounts)
        )

        self._main_account = main_account
        self._dependent_accounts = dependent_accounts

        return response

    async def async_get_accounts_list(self, code: Optional[AccountCode] = None):
        if code is None:
            code = self._username

        response = await GetLSListByLS.async_request(self, code)

        return list(map(self._make_account_from_response, response.data))

    async def async_get_account_info(self, code: Optional[AccountCode] = None):
        if code is None:
            code = self._username

        response = await GetInfo.async_request(self, code)

        return response


@attr.s(kw_only=True, frozen=True, slots=True)
class Indication(DataMapping):
    meter_identifier: str = attr.ib(repr=False)
    taken_on: date = attr.ib()
    meter_code: str = attr.ib()
    status: int = attr.ib()
    zones: Mapping[str, int] = attr.ib(converter=MappingProxyType)


ZONE_CODES_MAPPING = {
    "pik": "t1",
    "night": "t2",
    "ppik": "t3",
}


@attr.s(kw_only=True, frozen=True, slots=True)
class Payment(DataMapping):
    transaction_id: str = attr.ib()
    paid_at: datetime = attr.ib()
    source: str = attr.ib()
    amount: float = attr.ib()


@attr.s(kw_only=True, frozen=True, slots=True)
class Account(DataMapping):
    api: "TNSEnergoAPI" = attr.ib(repr=False)
    address: str = attr.ib()
    debt: float = attr.ib()
    code: str = attr.ib()
    email: str = attr.ib()
    digital_invoices_ignored: bool = attr.ib()
    digital_invoices_email: str = attr.ib()
    digital_invoices_enabled: bool = attr.ib()
    digital_invoices_email_comment: str = attr.ib()
    is_controlled: bool = attr.ib()
    is_controlling: bool = attr.ib()
    controlled_by_code: str = attr.ib()

    @property
    def balance(self) -> float:
        return -self.debt

    async def async_get_meters(self) -> Mapping[str, "Meter"]:
        response = await SendIndicationsPage.async_request(self.api, self.code)

        meters = {}
        for meter_id, zone_data_list in response.counters.items():
            if not zone_data_list:
                continue
            first_tariff = next(iter(zone_data_list))
            meters[first_tariff.code] = Meter(
                account=self,
                identifier=meter_id,
                code=first_tariff.code,
                can_delete=first_tariff.can_delete,
                checkup_date=first_tariff.checkup_date,
                checkup_status=first_tariff.checkup_status,
                checkup_url=first_tariff.checkup_url,
                last_checkup_date=first_tariff.last_checkup_date,
                manufactured_date=first_tariff.manufactured_date,
                transmission_coefficient=first_tariff.transmission_coefficient,
                last_indications_date=first_tariff.last_indications_date,
                install_location=first_tariff.install_location,
                model=first_tariff.model,
                precision=first_tariff.precision,
                status=first_tariff.status,
                service_name=first_tariff.service_name,
                service_number=first_tariff.service_number,
                tariff_count=first_tariff.zone_count,
                type=first_tariff.type,
                zones=MappingProxyType(
                    {
                        ("t" + str(zone.index + 1)): MeterZone(
                            identifier=zone.identifier,
                            index=zone.index,
                            name=zone.name.strip() or None,
                            last_indication=zone.last_indication,
                            max_indication_difference=zone.max_indication_difference,
                            closing_indication=zone.closing_indication,
                            label=zone.label,
                        )
                        for zone in zone_data_list
                    }
                ),
            )

        return meters

    async def async_get_payments(
        self,
        start: Optional[Union[datetime, date]] = None,
        end: Optional[Union[datetime, date]] = None,
    ):
        start, end = process_start_end_arguments(start, end)

        response = await GetPaymentsPage.async_request(self.api, self.code)

        payments = []

        for year, payments_data_list in response.history.items():
            for payment in payments_data_list:
                paid_at = payment.datetime or datetime.fromordinal(payment.date.toordinal())
                if start <= paid_at <= end:
                    payments.append(
                        Payment(
                            transaction_id=payment.transaction_id,
                            paid_at=paid_at,
                            source=payment.source,
                            amount=payment.amount,
                        )
                    )

        return payments

    async def async_get_last_payment(self) -> Optional[Payment]:
        payments = sorted(await self.async_get_payments(), key=lambda x: x.paid_at, reverse=True)
        return next(iter(payments)) if payments else None

    async def async_get_indications(
        self,
        start: Optional[Union[datetime, date]] = None,
        end: Optional[Union[datetime, date]] = None,
        meter_codes: Optional[Union[str, Iterable[str]]] = None,
    ):
        start, end = process_start_end_arguments(start, end)
        start_date, end_date = start.date(), end.date()

        response = await GetReadingsHistPage.async_request(self.api, self.code)

        if isinstance(meter_codes, str):
            meter_codes = (meter_codes,)
        elif meter_codes is not None:
            meter_codes = tuple(meter_codes)

        return [
            Indication(
                taken_on=date_,
                meter_identifier=meter,
                meter_code=data.meter_code,
                status=data.status or 0,
                zones=MappingProxyType(
                    {
                        ZONE_CODES_MAPPING[zone_code]: reading.value
                        for zone_code, reading in data.readings.items()
                    }
                ),
            )
            for year, date_meter_map in response.history.items()
            for date_, meter_data_map in date_meter_map.items()
            if start_date <= date_ <= end_date
            for meter, data in meter_data_map.items()
            if meter_codes is None or data.meter_code in meter_codes
        ]

    async def async_get_last_indication(
        self, meter_code: Optional[str] = None
    ) -> Optional[Indication]:
        readings = sorted(
            await self.async_get_indications(meter_code),
            key=lambda x: x.taken_on,
        )
        return next(iter(readings)) if readings else None


@attr.s(kw_only=True, frozen=True, slots=True)
class MeterZone(DataMapping):
    identifier: str = attr.ib()
    index: int = attr.ib()
    name: Optional[str] = attr.ib()
    last_indication: Optional[int] = attr.ib()
    max_indication_difference: float = attr.ib()
    closing_indication: Optional[float] = attr.ib()
    label: str = attr.ib()


@attr.s(kw_only=True, frozen=False, slots=True)
class Meter(DataMapping):
    account: "Account" = attr.ib(repr=False)
    code: str = attr.ib()
    can_delete: bool = attr.ib()
    checkup_date: date = attr.ib()
    checkup_status: int = attr.ib()
    checkup_url: str = attr.ib()
    last_checkup_date: date = attr.ib()
    manufactured_date: date = attr.ib()
    identifier: str = attr.ib()
    transmission_coefficient: float = attr.ib()
    last_indications_date: Optional[date] = attr.ib()
    install_location: str = attr.ib()
    model: str = attr.ib()
    precision: int = attr.ib()
    status: str = attr.ib()
    service_name: str = attr.ib()
    service_number: str = attr.ib()
    tariff_count: int = attr.ib()
    type: int = attr.ib()
    zones: Mapping[str, MeterZone] = attr.ib()

    async def async_get_indications(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ):
        return await self.account.async_get_indications(start, end, self.code)

    async def async_get_last_indication(self) -> Optional[Indication]:
        return await self.account.async_get_last_indication(self.code)

    async def async_send_indications(
        self,
        t1: Optional[SupportsInt] = None,
        t2: Optional[SupportsInt] = None,
        t3: Optional[SupportsInt] = None,
        *,
        ignore_values: bool = False,
        **kwargs,
    ):
        # @TODO: this assumes multi-zone meters may accept arbitrary indications count

        if t1 is not None:
            kwargs["t1"] = t1

        if t2 is not None:
            kwargs["t2"] = t2

        if t3 is not None:
            kwargs["t3"] = t3

        zones = self.zones

        if kwargs.keys() - self.zones.keys():
            raise TypeError("invalid indications count provided")

        send_indications = []

        for zone_id, value in kwargs.items():
            zone = zones[zone_id]
            value = int(value)

            if not (ignore_values or value > (zone.last_indication or 0)):
                raise ValueError("invalid indication provided (less than previous)")

            send_indications.append(
                NewIndication(
                    meter_number=self.code,
                    indication=value,
                    label=zone.label,
                    index=zone.index,
                    identifier=zone.identifier,
                )
            )

        return await SendIndications.async_request(
            self.account.api,
            self.account.code,
            send_indications,
        )
