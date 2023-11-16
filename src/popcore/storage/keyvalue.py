import os
from typing import Any, Dict, Optional

import fsspec
import yaml
from .core import (
    Serializer, PlayerSerializer, PersistentObject,
    KeyValue
)


class KeyValueFile(KeyValue[PersistentObject]):
    def __init__(
        self,
        path: str,
        file: fsspec.AbstractFileSystem,
        serializer: Optional[Serializer] = None,
    ) -> None:
        super().__init__(
            serializer=serializer,
        )
        self.path = path
        self._file = file
        self._load_from_file()

    def _write(self, key: str, value: PersistentObject):
        yaml.dump({
            key: value,
        }, self._file, explicit_start=True, explicit_end=True)
        super()._write(key, value)

    def _load_from_file(self):
        for entry in yaml.safe_load_all(self._file):
            for k, v in entry.items():
                super()._write(k, v)


class KeyValueSerializer(Serializer[str, KeyValueFile]):

    def __init__(
        self,
        path: str,
        filesystem: fsspec.AbstractFileSystem
    ) -> None:
        self._path = path
        self._fs = filesystem

    def serialize(self, path: str) -> KeyValueFile:
        file = self._fs.open(
            os.path.join(self._path, path),
            mode="a+" if self._fs.exists(path) else "w+"
        )
        return KeyValueFile(
            path=path,
            file=file,
            serializer=PlayerSerializer()
        )

    def deserialize(self, file: KeyValueFile) -> str:
        return file


class KeyValueFileStore(KeyValue[KeyValueFile]):
    def __init__(
        self,
        path: str,
        filesystem: str = 'file',
        filesystem_options: Dict[str, Any] | None = None,
    ) -> None:
        self._fs: fsspec.AbstractFileSystem = fsspec.filesystem(
            filesystem, storage_options=filesystem_options)
        self._fs.makedirs(path, exist_ok=True)
        super().__init__(serializer=KeyValueSerializer(path, self._fs))
