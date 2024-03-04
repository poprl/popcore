from typing import Dict, Iterable, Optional
import fsspec
import yaml
from .core import (
    Memory, Serializer, MemoryObject, File
)


class KeyValueFile(File[MemoryObject]):
    def __init__(
        self,
        path: str,
        filesystem: fsspec.AbstractFileSystem,
        serializer: Optional[Serializer[MemoryObject, Dict]] = None,
    ) -> None:
        super().__init__(path, filesystem, serializer)
        self._file = filesystem.open(self._path, mode="a+")
        self._cache = Memory[MemoryObject]()
        self._serializer = serializer

    def write(self, key: str, value: MemoryObject):
        self._cache.write(key, value)

        if self._serializer:
            value = self._serializer.serialize(value)

        yaml.dump({
            key: value,
        }, self._file, explicit_start=True, explicit_end=True)

    def read(self, key: str) -> MemoryObject:
        if key not in self._cache:
            self._read_all(self._file)
        if key not in self._cache:
            raise ValueError()

        return self._cache[key]

    def _read_all(self):
        for keys in yaml.safe_load_all(self._file):
            for k, v in keys.items():
                if k not in self._cache:
                    if self._serializer:
                        v = self._serializer.deserialize(v)
                    self._cache.write(k, v)

    def remove(self, key: str) -> MemoryObject:
        raise NotImplementedError()

    def delete(self):
        self._cache.delete()
        self._file.close()
        self._filesystem.rm_file(self._path)

    def iter(self) -> Iterable[MemoryObject]:
        return self._cache.iter()

    def exists(self, key: str) -> bool:
        return key in self._cache
