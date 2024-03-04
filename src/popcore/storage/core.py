from abc import ABC, abstractmethod
from typing import (
    Dict, Generic, Iterable, TypeVar
)
import fsspec

MemoryObject = TypeVar("MemoryObject")
PersistentObject = TypeVar("PersistentObject")


class Serializer(ABC, Generic[MemoryObject, PersistentObject]):

    @abstractmethod
    def serialize(self, obj: MemoryObject) -> PersistentObject:
        raise NotImplementedError()

    @abstractmethod
    def deserialize(
        self, store: PersistentObject
    ) -> MemoryObject:
        raise NotImplementedError


class Store(ABC, Generic[MemoryObject]):
    @abstractmethod
    def remove(self, key: str) -> MemoryObject:
        raise NotImplementedError()

    @abstractmethod
    def delete(self):
        raise NotImplementedError()

    @abstractmethod
    def write(self, key: str, value: MemoryObject):
        raise NotImplementedError()

    @abstractmethod
    def read(self, key: str) -> MemoryObject:
        raise NotImplementedError()

    @abstractmethod
    def exists(self, key: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def iter(self) -> Iterable[MemoryObject]:
        raise NotImplementedError()

    def __contains__(self, key: str):
        return self.exists(key)

    def __iter__(self):
        return self.iter()

    def __getitem__(self, key: str) -> MemoryObject:
        return self.read(key)

    def __setitem__(self, key: str, value: MemoryObject):
        return self.write(key, value)


class Memory(Store[MemoryObject]):

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self._mem: Dict[str, MemoryObject] = dict()

    def remove(self, key: str) -> MemoryObject:
        return self._mem.pop(key)

    def delete(self):
        self._mem.clear()

    def write(self, key: str, value: MemoryObject):
        self._mem[key] = value

    def read(self, key: str) -> MemoryObject:
        return self._mem[key]

    def exists(self, key: str) -> bool:
        return key in self._mem

    def iter(self) -> Iterable[MemoryObject]:
        return self._mem.__iter__()

    def __contains__(self, key: str):
        return self.exists(key)

    def __iter__(self) -> Iterable[MemoryObject]:
        return self.iter()

    def __getitem__(self, key: str) -> MemoryObject:
        return self.read(key)

    def __setitem__(self, key: str, value: MemoryObject):
        return self.write(key, value)


class File(Store[MemoryObject]):

    def __init__(
        self,
        path: str,
        filesystem: fsspec.AbstractFileSystem,
        serializer: Serializer[MemoryObject, PersistentObject]
    ) -> None:
        super().__init__()
        self._path = path
        self._filesystem = filesystem
        self._serializer = serializer


class MultifileStore(Store[File]):

    def __init__(
        self,
        path: str,
        filesystem: fsspec.AbstractFileSystem,
    ) -> None:
        self._path = path
        self._cache = Memory[MemoryObject]()
        self._filesystem = filesystem
        self._filesystem.makedirs(path, exist_ok=True)

    def write(self, key: str, value: File):
        assert key not in self._cache
        self._cache[key] = value

    def read(self, key: str) -> File:
        assert key in self._cache
        return self._cache[key]

    def delete(self):
        for key in self._cache:
            self._cache[key].delete()
        self._cache.delete()
        self._filesystem.delete(self._path, recursive=True)

    def remove(self, key: str):
        assert key in self._cache
        store: File = self._cache.remove(key)
        store.delete()

    def exists(self, key: str) -> bool:
        return key in self._cache

    def iter(self) -> Iterable[File]:
        return self._cache.iter()

    @property
    def path(self):
        return self._path
