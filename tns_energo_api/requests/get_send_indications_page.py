from datetime import date
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Optional, Sequence, TYPE_CHECKING, Tuple, Union

import attr

from tns_energo_api.converters import (
    DataMapping,
    META_SOURCE_DATA_KEY,
    RequestMapping,
    conv_bool,
    conv_date_optional,
    conv_float,
    conv_int,
    conv_str_optional,
    conv_str_stripped,
    wrap_optional_eval,
    wrap_optional_none,
    wrap_str_stripped,
)
from tns_energo_api.exceptions import EmptyResultException

if TYPE_CHECKING:
    from tns_energo_api import TNSEnergoAPI


@attr.s(kw_only=True, frozen=True, slots=True)
class ZoneData(DataMapping):
    identifier: str = attr.ib(
        converter=conv_str_stripped,
        metadata={META_SOURCE_DATA_KEY: "RowID"},
    )
    index: int = attr.ib(
        converter=conv_int,
        metadata={META_SOURCE_DATA_KEY: "NomerTarifa"},
    )
    name: str = attr.ib(
        converter=conv_str_stripped,
        metadata={META_SOURCE_DATA_KEY: "NazvanieTarifa"},
    )
    last_indication: Optional[int] = attr.ib(
        converter=wrap_optional_none(wrap_str_stripped(wrap_optional_eval(int))),
        metadata={META_SOURCE_DATA_KEY: "PredPok"},
    )
    transmission_coefficient: float = attr.ib(
        converter=conv_float,
        metadata={META_SOURCE_DATA_KEY: "KoefTrans"},
    )
    max_indication_difference: float = attr.ib(
        converter=conv_float,
        metadata={META_SOURCE_DATA_KEY: "MaxPok"},
    )
    type: int = attr.ib(
        converter=conv_int,
        metadata={META_SOURCE_DATA_KEY: "Type"},
    )
    can_delete: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "Can_delete"},
    )
    closing_indication: Optional[float] = attr.ib(
        converter=wrap_optional_none(wrap_str_stripped(wrap_optional_eval(float))),
        metadata={META_SOURCE_DATA_KEY: "zakrPok"},
    )
    label: str = attr.ib(
        converter=conv_str_stripped,
        metadata={META_SOURCE_DATA_KEY: "Label"},
    )
    sort: int = attr.ib(
        converter=conv_int,
        metadata={META_SOURCE_DATA_KEY: "sort"},
    )
    checkup_status: int = attr.ib(
        converter=conv_int,
        metadata={META_SOURCE_DATA_KEY: "DatePoverStatus"},
    )
    checkup_url: Optional[str] = attr.ib(
        converter=conv_str_optional,
        metadata={META_SOURCE_DATA_KEY: "DatePoverURL"},
        default=None,
    )
    checkup_date: Optional[date] = attr.ib(
        converter=conv_date_optional,
        metadata={META_SOURCE_DATA_KEY: "DatePover"},
        default=None,
    )
    status: str = attr.ib(
        converter=conv_str_stripped,
        metadata={META_SOURCE_DATA_KEY: "RaschSch"},
    )
    install_location: str = attr.ib(
        converter=conv_str_stripped,
        metadata={META_SOURCE_DATA_KEY: "MestoUst"},
    )
    manufactured_date: Optional[date] = attr.ib(
        converter=conv_date_optional,
        metadata={META_SOURCE_DATA_KEY: "GodVipuska"},
        default=None,
    )
    last_checkup_date: Optional[date] = attr.ib(
        converter=conv_date_optional,
        metadata={META_SOURCE_DATA_KEY: "DatePosledPover"},
        default=None,
    )
    model: str = attr.ib(
        converter=conv_str_stripped,
        metadata={META_SOURCE_DATA_KEY: "ModelPU"},
    )
    zone_count: int = attr.ib(
        converter=conv_int,
        metadata={META_SOURCE_DATA_KEY: "Tarifnost"},
    )
    last_indications_date: Optional[date] = attr.ib(
        converter=conv_date_optional,
        metadata={META_SOURCE_DATA_KEY: "DatePok"},
        default=None,
    )
    service_number: str = attr.ib(
        converter=conv_str_stripped,
        metadata={META_SOURCE_DATA_KEY: "NomerUslugi"},
    )
    service_name: str = attr.ib(
        converter=conv_str_stripped,
        metadata={META_SOURCE_DATA_KEY: "NazvanieUslugi"},
    )
    code: str = attr.ib(
        converter=conv_str_stripped,
        metadata={META_SOURCE_DATA_KEY: "ZavodNomer"},
    )
    precision: int = attr.ib(
        converter=conv_int,
        metadata={META_SOURCE_DATA_KEY: "Razradnost"},
    )


def converter__counters(
    value: Union[
        Mapping[
            Union[str, int],
            Iterable[
                Union[
                    Mapping[str, Any],
                    ZoneData,
                ],
            ],
        ],
        Iterable,
    ],
) -> Mapping[str, Tuple[ZoneData, ...]]:
    if not isinstance(value, Mapping):
        if isinstance(value, Sequence) and len(value) == 0:
            return {}
        raise TypeError("invalid mapping")

    return MappingProxyType(
        {
            meter_id: tuple(
                sorted(
                    (
                        (
                            tariff_data
                            if isinstance(tariff_data, ZoneData)
                            else ZoneData.from_response(tariff_data)
                        )
                        for tariff_data in tariff_data_list
                    ),
                    key=lambda x: (x.sort, x.index),
                )
            )
            for meter_id, tariff_data_list in value.items()
        }
    )


@attr.s(kw_only=True, frozen=True, slots=True)
class SendIndicationsPage(RequestMapping):
    @classmethod
    async def async_request_raw(cls, on: "TNSEnergoAPI", code: str):
        return await on.async_req_get(
            ("region", on.region, "action", "getSendReadingsPage", "ls", code, "json"),
        )

    @classmethod
    async def async_request(cls, on: "TNSEnergoAPI", code: str):
        result = await cls.async_request_raw(on, code)
        if result is None:
            raise EmptyResultException("Response result is empty")
        return cls.from_response(result)

    status: str = attr.ib(
        converter=conv_str_stripped,
        metadata={META_SOURCE_DATA_KEY: "STATUS"},
    )
    counters: Mapping[str, Sequence[ZoneData]] = attr.ib(
        converter=converter__counters,
        metadata={META_SOURCE_DATA_KEY: "counters"},
    )
