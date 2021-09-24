import inspect
from abc import ABC
from datetime import date, datetime
from typing import Any, Callable, Mapping, Optional, Type, TypeVar, Union

import attr

from tns_energo_api.exceptions import ResponseException


def conv_bool(value: Union[bool, str]) -> bool:
    if value is True or value is False:
        return value
    if value is None:
        return False
    value = str(value).strip().lower()
    if value in ("false", "0"):
        return False
    if value in ("true", "1"):
        return True
    raise ValueError("invalid boolean value")


def conv_float(value: Union[float, str]) -> float:
    return float(str(value).strip())


def conv_int(value: Union[int, str]) -> int:
    return int(str(value).strip())


def conv_date_optional(value: Optional[Union[date, str]]) -> Optional[date]:
    if value is None:
        return None

    if isinstance(value, date):
        return value

    value = str(value).strip()
    if not value:
        return None

    try:
        dt = datetime.strptime(value, "%d.%m.%y")
    except ValueError:
        dt = datetime.strptime(value, "%d.%m.%Y")

    return dt.date()


def conv_datetime_optional(value: Optional[Union[datetime, str]]) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    value = str(value).strip()
    if not value:
        return None

    if len(value) != 14:
        raise ValueError("datetime can only be converted from long string (14len)")

    return datetime.strptime(value, "%Y%m%d%H%M%S")


_T = TypeVar("_T")
_RT = TypeVar("_RT")
_T2 = TypeVar("_T2")


def conv_optional_eval(value: Optional[_T]) -> Optional[_T]:
    return value or None


def wrap_optional_eval(conv: Callable[[_T], _RT]) -> Callable[[Optional[_T]], Optional[_RT]]:
    return lambda value: conv(value) if value else None


def conv_optional_none(value: Optional[_T]) -> Optional[_T]:
    return None if value is None else value


def wrap_default_none(
    conv: Callable[[_T], _RT], default: Union[_T2, Callable[[], _T2]]
) -> Callable[[Optional[_T]], Union[_RT, _T2]]:
    if callable(default):
        return lambda value: conv(default() if value is None else value)
    return lambda value: conv(default if value is None else value)


def wrap_optional_none(conv: Callable[[_T], _RT]) -> Callable[[Optional[_T]], Optional[_RT]]:
    return lambda value: None if value is None else conv(value)


def conv_str_stripped(value: Any) -> str:
    return str(value).strip()


def conv_str_optional(value: Optional[Any]) -> Optional[str]:
    return conv_str_stripped(value) if value else None


def wrap_str_stripped(conv: Callable[[str], _RT]) -> Callable[[Any], _RT]:
    return lambda value: conv(conv_str_stripped(value))


META_SOURCE_DATA_KEY = "source_data_key"


class DataMapping(Mapping, ABC):
    _meta_search: Mapping[str, str] = NotImplemented

    def __init_subclass__(cls, **kwargs):
        if not inspect.isabstract(cls):
            if attr.has(cls):
                cls._meta_search = {
                    field.metadata[META_SOURCE_DATA_KEY]: field.name
                    for field in attr.fields(cls)
                    if META_SOURCE_DATA_KEY in field.metadata
                }
        return super().__init_subclass__(**kwargs)

    def convert_to(self, cls: Type[_T], **kwargs) -> _T:
        if not attr.has(cls):
            raise TypeError("can only evolve to an attrs-decorated class")
        init_args = {
            key: getattr(self, key) for key in attr.fields_dict(cls).keys() if hasattr(self, key)
        }
        init_args.update(kwargs)
        return cls(**init_args)

    @classmethod
    def convert(cls, other, **kwargs):
        if not attr.has(cls):
            raise TypeError("can only evolve to an attrs-decorated class")
        init_args = {
            key: getattr(other, key) for key in attr.fields_dict(cls).keys() if hasattr(other, key)
        }
        init_args.update(kwargs)
        return cls(**init_args)

    @classmethod
    def from_response(cls, data: Mapping[str, Any], **kwargs):
        if not attr.has(cls):
            raise TypeError("DataMapping.from_response may only be used on attrs classes")

        init_args = {}

        # noinspection PyDataclass
        for field in attr.fields(cls):
            data_field = field.metadata.get(META_SOURCE_DATA_KEY, field.name)
            if data_field and data_field in data:
                init_args[field.name.lstrip("_")] = data[data_field]

        init_args.update(kwargs)

        return cls(**init_args)  # type: ignore[call-arg]

    def __len__(self):
        return len(self._meta_search)

    def __iter__(self):
        return iter(self._meta_search)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, self._meta_search[item])


class RequestMapping(DataMapping):
    @classmethod
    def from_response(cls, data: Mapping[str, Any], **kwargs):
        if not conv_bool(data["result"]):
            code = data.get("error")
            if code is None:
                code = data.get("errorCode")
                if code is None:
                    code = -1

            msg = data.get("errMsg")
            if msg is None:
                msg = data.get("errorMessage")
                if msg is None:
                    msg = data.get("errorHeader")
                    if msg is None:
                        msg = "<no description provided>"

            raise ResponseException(code, msg)

        return super().from_response(data, **kwargs)
