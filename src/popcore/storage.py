from .hooks import PostCommitHook
from . import Population, Player


class Storage:
    pass


class LocalStorage:
    pass


class MemoryStorage:
    pass


class GoogleCloudStorage:
    pass


class WandbStorage:
    pass


if __name__ == "__main__":
    store = Storage()
    store.commit()
