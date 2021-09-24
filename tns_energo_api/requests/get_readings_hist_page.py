__all__ = ("GetReadingsHistPage",)

from datetime import date
from typing import Any, Mapping, Optional, TYPE_CHECKING, Union

import attr

from tns_energo_api.converters import (
    DataMapping,
    META_SOURCE_DATA_KEY,
    RequestMapping,
    conv_date_optional,
    conv_int,
    conv_str_stripped,
    wrap_optional_eval,
)
from tns_energo_api.exceptions import EmptyResultException

if TYPE_CHECKING:
    from tns_energo_api import TNSEnergoAPI


@attr.s(kw_only=True, frozen=True, slots=True)
class ReadingData(DataMapping):
    label: str = attr.ib(converter=conv_str_stripped, metadata={META_SOURCE_DATA_KEY: "label"})
    value: int = attr.ib(converter=conv_int, metadata={META_SOURCE_DATA_KEY: "value"})


def converter__readings(value: Mapping[str, Union[ReadingData, Mapping[str, Any]]]):
    retval = {}

    if not value:
        return retval
    elif not isinstance(value, Mapping):
        raise TypeError(type(value))

    for zone, data in value.items():
        if not data:
            continue
        elif not isinstance(value, Mapping):
            raise TypeError(type(value))
        elif not isinstance(value, ReadingData):
            data = ReadingData.from_response(data)

        retval[zone] = data

    return retval


@attr.s(kw_only=True, frozen=True, slots=True)
class GetReadingsHistPageData(DataMapping):
    meter_code: str = attr.ib(
        converter=conv_str_stripped,
        metadata={META_SOURCE_DATA_KEY: "number"},
    )
    status: Optional[int] = attr.ib(
        converter=wrap_optional_eval(conv_int),
        metadata={META_SOURCE_DATA_KEY: "status"},
    )
    readings: Mapping[str, ReadingData] = attr.ib(
        converter=converter__readings,
        factory=dict,
        metadata={META_SOURCE_DATA_KEY: "readings"},
    )


def converter__history(
    value: Mapping[
        Union[int, str],
        Mapping[Union[date, str], Mapping[str, Union[Mapping[str, Any], GetReadingsHistPageData]]],
    ]
):
    retval = {}

    if not value:
        return retval
    elif not isinstance(value, Mapping):
        raise TypeError(type(value))

    for year, date_meter_map in value.items():
        if not date_meter_map:
            continue
        elif not isinstance(date_meter_map, Mapping):
            raise TypeError(type(date_meter_map))

        year = conv_int(year)

        for date_, meter_data_map in date_meter_map.items():
            if not meter_data_map:
                continue

            if not isinstance(meter_data_map, Mapping):
                raise TypeError(type(meter_data_map))

            date_ = conv_date_optional(date_)

            if date_ is None:
                continue

            for meter, data in meter_data_map.items():
                if not data:
                    continue
                elif not isinstance(data, Mapping):
                    raise TypeError(type(data))
                elif not isinstance(data, GetReadingsHistPageData):
                    data = GetReadingsHistPageData.from_response(data)

                retval.setdefault(year, {}).setdefault(date_, {})[meter] = data

    return retval


@attr.s(kw_only=True, frozen=True, slots=True)
class GetReadingsHistPage(RequestMapping):
    @classmethod
    async def async_request_raw(cls, on: "TNSEnergoAPI", code: str):
        return await on.async_req_get(
            ("region", on.region, "action", "getReadingsHistPage", "ls", code, "json")
        )

    @classmethod
    async def async_request(cls, on: "TNSEnergoAPI", code: str):
        result = await cls.async_request_raw(on, code)
        if result is None:
            raise EmptyResultException("Response result is empty")
        return cls.from_response(result)

    history: Mapping[int, Mapping[date, Mapping[str, GetReadingsHistPageData]]] = attr.ib(
        converter=converter__history,
        metadata={META_SOURCE_DATA_KEY: "history"},
    )
