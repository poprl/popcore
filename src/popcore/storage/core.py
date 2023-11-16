from abc import ABC, abstractmethod
from typing import (
    Dict, Generic, List, TypeVar
)
from ..core import Player

PersistentObject = TypeVar("PersistentObject")
PersistenceFormat = TypeVar("PersistenceFormat")


class Serializer(ABC, Generic[PersistentObject, PersistenceFormat]):

    @abstractmethod
    def serialize(self, obj: PersistentObject) -> PersistenceFormat:
        raise NotImplementedError()

    @abstractmethod
    def deserialize(
        self, key_value_store: PersistenceFormat
    ) -> PersistentObject:
        raise NotImplementedError


class PlayerSerializer(Serializer[Player, dict]):

    def __init__(
        self,
        exclude_fields: List[str] = ['descendants']
    ) -> None:
        super().__init__()
        self._exclude_fields = exclude_fields

    def serialize(self, player: 'Player') -> dict:
        return {
            k: v for k, v in player.__dict__.items()
            if k not in self._exclude_fields
        }

    def deserialize(self, key_value_store: dict) -> 'Player':
        filtered = {
            k: v for k, v in key_value_store
            if k not in self._exclude_fields
        }
        return Player(**filtered)


class KeyValue(Generic[PersistentObject]):

    def __init__(
        self,
        serializer: Serializer[PersistentObject, PersistenceFormat],
    ) -> None:
        super().__init__()
        self._mem: Dict[str, PersistentObject] = dict()
        self._serializer = serializer

    def _write(self, key: str, value: PersistentObject):
        assert not self._exist(key)
        self._mem[key] = value

    def _read(self, key: str) -> PersistentObject:
        assert self._exist(key)
        return self._mem[key]

    def _exist(self, key: str) -> bool:
        return key in self._mem

    def _delete(self, key: str):
        return self._mem.pop(key)

    def __setitem__(self, key: str, value: PersistentObject):
        if self._serializer:
            value = self._serializer.serialize(value)
        self._write(key, value)

    def __getitem__(self, key: str) -> PersistentObject:
        value = self._read(
            key=key
        )
        if self._serializer:
            value = self._serializer.deserialize(value)
        return value

    def __contains__(self, name: str):
        return self._exist(name)
