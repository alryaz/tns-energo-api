from datetime import date
from typing import Any, Iterable, Mapping, NamedTuple, TYPE_CHECKING, Union

import attr

from tns_energo_api.converters import (
    DataMapping,
    META_SOURCE_DATA_KEY,
    RequestMapping,
    conv_bool,
    conv_date,
    conv_float,
)

if TYPE_CHECKING:
    from tns_energo_api import TNSEnergoAPI


@attr.s(kw_only=True, frozen=True, slots=True)
class ResultData(DataMapping):
    initial: float = attr.ib(
        converter=conv_float,
        metadata={META_SOURCE_DATA_KEY: "ВХСАЛЬДО"},
    )
    debt: float = attr.ib(
        converter=conv_float,
        metadata={META_SOURCE_DATA_KEY: "ЗАДОЛЖЕННОСТЬ"},
    )
    debt_disable: float = attr.ib(
        converter=conv_float,
        metadata={META_SOURCE_DATA_KEY: "ЗАДОЛЖЕННОСТЬОТКЛ"},
    )
    debt_penalty: float = attr.ib(
        converter=conv_float,
        metadata={META_SOURCE_DATA_KEY: "ЗАДОЛЖЕННОСТЬПЕНИ"},
    )
    debt_install: float = attr.ib(
        converter=conv_float,
        metadata={META_SOURCE_DATA_KEY: "ЗАДОЛЖЕННОСТЬПОДКЛ"},
    )
    period: date = attr.ib(
        converter=conv_date,
        metadata={META_SOURCE_DATA_KEY: "ЗАКРЫТЫЙМЕСЯЦ"},
    )
    charged_meter: float = attr.ib(
        converter=conv_float,
        metadata={META_SOURCE_DATA_KEY: "НАЧИСЛЕНОПОИПУ"},
    )
    recalculations: float = attr.ib(
        converter=conv_float,
        metadata={META_SOURCE_DATA_KEY: "ПЕРЕРАСЧЕТ"},
    )
    projected_meter: float = attr.ib(
        converter=conv_float,
        metadata={META_SOURCE_DATA_KEY: "ПРОГНОЗПОИПУ"},
    )
    loss: float = attr.ib(
        converter=conv_float,
        metadata={META_SOURCE_DATA_KEY: "СУМАПОТЕРИ"},
    )
    total: float = attr.ib(
        converter=conv_float,
        metadata={META_SOURCE_DATA_KEY: "СУММАКОПЛАТЕ"},
    )
    projected_communal: float = attr.ib(
        converter=conv_float,
        metadata={META_SOURCE_DATA_KEY: "СУММАОДНПРОГНОЗ"},
    )
    projected_penalty: float = attr.ib(
        converter=conv_float,
        metadata={META_SOURCE_DATA_KEY: "СУММАПЕНИПРОГНОЗ"},
    )
    paid: float = attr.ib(
        converter=conv_float,
        metadata={META_SOURCE_DATA_KEY: "СУММАПЛАТЕЖЕЙ"},
    )
    summaprognozna_ch: float = attr.ib(
        converter=conv_float,
        metadata={META_SOURCE_DATA_KEY: "СУММАПРОГНОЗНАЧ"},
    )
    is_meter_charged: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "ФНАЧИСЛЕНОПОИПУ"},
    )
    total_pseudo: float = attr.ib(
        converter=conv_float,
        metadata={META_SOURCE_DATA_KEY: "KOPLATEPSEVDO"},
    )


def _converter__data(value: Union[Mapping[str, Any], ResultData]) -> ResultData:
    if isinstance(value, ResultData):
        return value
    return ResultData.from_response(value)


class NewIndication(NamedTuple):
    meter_number: str
    indication: int
    label: str
    index: int
    identifier: str


@attr.s(kw_only=True, frozen=True, slots=True)
class SendIndications(RequestMapping):
    @classmethod
    async def async_request_raw(cls, on: "TNSEnergoAPI", code: str, data: Iterable[NewIndication]):
        return await on.async_req_post(
            ("region", on.region, "action", "sendReadings", "ls", code, "json"),
            list(
                map(
                    lambda x: dict(
                        zip(
                            ("counterNumber", "newPok", "label", "nomerTarifa", "rowID"),
                            map(str, x),
                        )
                    ),
                    data,
                ),
            ),
            "readings",
        )

    @classmethod
    async def async_request(cls, on: "TNSEnergoAPI", code: str, data: Iterable[NewIndication]):
        return cls.from_response(await cls.async_request_raw(on, code, data))

    result: bool = attr.ib(
        converter=conv_bool,
        metadata={META_SOURCE_DATA_KEY: "result"},
    )
    data: "ResultData" = attr.ib(
        converter=_converter__data,
        metadata={META_SOURCE_DATA_KEY: "data"},
    )
