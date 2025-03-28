from __future__ import annotations

import dataclasses
import enum
import logging
from typing import Dict, List, Type, Optional, TypeVar, Any, Callable, Iterator

logger = logging.getLogger(__name__)


class PendingValue:
    def __hash__(self):
        return id(self)

    def __repr__(self):
        return f"<PendingValue #{id(self)}>"


class Item:
    def serialize(self, only: Optional[Iterator[str]] = None) -> Dict:
        data = {}
        for field in dataclasses.fields(self):
            name = field.name
            if only is not None and name not in only:
                continue
            value = getattr(self, name)
            if isinstance(value, enum.Enum):
                data[name] = value.value
            elif not isinstance(value, PendingValue):
                data[name] = value
        return data


CollectionType = TypeVar("CollectionType", bound=Item)


class Collection:
    primary_key_field_name: str
    type: Type[CollectionType]

    _members: List[CollectionType]

    def __init__(self, *members: CollectionType):
        for member in members:
            if not isinstance(member, self.type):
                raise ValueError(
                    f"Invalid member {member}. Required type is {self.type}."
                )
        self._members = list(members)

    def __iter__(self):
        return iter(self._members)

    def __len__(self):
        return len(self._members)

    def __bool__(self):
        return bool(self._members)

    def __contains__(self, item):
        try:
            sub_collection = self.filter(
                **{
                    self.primary_key_field_name: getattr(
                        item, self.primary_key_field_name
                    )
                }
            )
            return bool(sub_collection)
        except ValueError:
            return False

    def __getitem__(self, index):
        return self._members[index]

    def __add__(self, other: CollectionType):
        if isinstance(other, Collection):
            self._members += other._members
        else:
            self._members.append(other)
        return self

    def filter(
        self, fn: Optional[Callable[[Item], bool]] = None, **fields: Any
    ) -> Collection:
        if fn and fields:
            raise ValueError("Use either fn or **fields.")

        collection_type = type(self)
        members = []

        for item in self:
            if fn and fn(item):
                members.append(item)

            for field_name, field_value in fields.items():
                if getattr(item, field_name) != field_value:
                    break
            else:
                members.append(item)

        return collection_type(*members)

    def get(
        self, fn: Optional[Callable[[Item], bool]] = None, **fields: Any
    ) -> CollectionType:
        filtered = self.filter(fn, **fields)
        if not filtered:
            raise ValueError(f"No objects found - {fn=} {fields=}.")
        if len(filtered) > 1:
            raise ValueError(f"Multiple objects found - {fn=} {fields=}.")
        return filtered[0]

    def distinct(self) -> Collection:
        distinct_collections = {}

        for item in self:
            distinct_collections[getattr(item, self.primary_key_field_name)] = item

        return type(self)(*distinct_collections.values())
