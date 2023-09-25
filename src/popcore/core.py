import abc
from typing import Generic, List, TypeVar


OUTCOME = TypeVar("OUTCOME")
STEP = TypeVar("STEP")


class Player(abc.ABC):
    name: str

    def __init__(self, name: str):
        self.name = name


class Team(Player):
    members: "list[Player]"

    def __init__(self, name: str, members: "list[Player]"):
        self.members = members
        super().__init__(name)


class Interaction(Generic[OUTCOME]):
    """_summary_
        players: players involved in the game
        scores: outcomes for each player involved in the game
    """

    def __init__(
        self,
        players: List[Player],
        outcomes: List[OUTCOME],
        timestep: int = 0
    ):
        """_summary_

        Args:
            players (List[Player]): _description_
            outcomes (List[OUTCOME]): _description_
        """
        assert len(players) == len(outcomes)
        assert timestep >= 0
        self._players = players
        self._outcomes = outcomes
        self._timestep = timestep

    @property
    def players(self):
        return self._players

    @property
    def outcomes(self):
        return self._outcomes

    @property
    def timestep(self):
        return self._timestep


class Population:

    def __init__(
        self,
        id: str,
        parent: 'Population' | None = None
    ) -> None:
        self._id = id
        self._players: dict[str, Player] = dict()
        self._parent = parent

    @property
    def id(self):
        return self._id

    def add(
        self,
        id: str,
        player: Player
    ):
        pass

    def at(self, generation: int | None = None):
        pass

    def commit(self, *args):
        pass

    def __enter__(self):
        pass

    def __exit__(
        self, exc_type,
        exc_val, exc_tb
    ):
        pass
