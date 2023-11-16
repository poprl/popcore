
from typing import Any, Dict
import fsspec
from .core import Serializer
from .keyvalue import KeyValue


class BinaryFile:
    pass


class BinaryFileSerializer(Serializer[str, BinaryFile]):
    def __init__(self, path, fs) -> None:
        super().__init__()
        self._path = path
        self._fs = fs

    def serialize(self, obj: str) -> BinaryFile:
        return super().serialize(obj)

    def deserialize(self, key_value_store: BinaryFile) -> str:
        return super().deserialize(key_value_store)


class BinaryFileStore(KeyValue[BinaryFile]):
    def __init__(
        self,
        path: str,
        filesystem: str = 'file',
        filesystem_options: Dict[str, Any] | None = None,
    ) -> None:
        self._fs: fsspec.AbstractFileSystem = fsspec.filesystem(
            filesystem, storage_options=filesystem_options)
        self._fs.makedirs(path, exist_ok=True)
        super().__init__(serializer=BinaryFileSerializer(path, self._fs))
