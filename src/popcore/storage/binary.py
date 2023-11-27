
import fsspec
from .core import Serializer
from .keyvalue import Memory


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


class BinaryFileStore(Memory[BinaryFile]):
    def __init__(
        self,
        path: str,
        filesystem: fsspec.AbstractFileSystem,
    ) -> None:
        self._fs = filesystem
        self._fs.makedirs(path, exist_ok=True)
        super().__init__(serializer=BinaryFileSerializer(path, self._fs))
        self.path = path

    def _delete(self):
        [self._fs.rm_file(v.path) for k, v in self._mem.items()]
        self._fs.rmdir(self.path)
        super()._delete()
