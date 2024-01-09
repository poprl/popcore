from dataclasses import dataclass
from itertools import combinations
from typing import (
    Any, Generic, Iterable, List,
    Optional, TypeVar, Union
)
import numpy as np


GameOutcome = TypeVar("GameOutcome")


@dataclass
class Player:
    """
        Player abstraction
    """
    id: str

    def __eq__(self, other: 'Player') -> bool:
        return self.id == other.id

    def __str__(self) -> str:
        return self.id

    def __repr__(self) -> str:
        return f"Player(id={self.id})"


PlayerLike = Union[Player, str]


@dataclass
class Coalition(Player):
    """
       A coalition is a collection of players that act together.
    """
    members: list[Player]

    def __repr__(self) -> str:
        return f"Coalition({str([player for player in self.members])})"


@dataclass
class Interaction(Generic[GameOutcome]):
    """
        Records an interaction between players, and each
        player outcome.

        players: players involved in the game
        outcomes: outcomes for each player involved in the game
    """

    def __init__(
        self, players: Iterable[PlayerLike], outcomes: Iterable[GameOutcome]
    ):
        self._players = np.array(players)
        self._outcomes = np.array(outcomes)

        # TODO: exception handling
        if self._players.shape[-1] < 2:
            raise ValueError("interaction.at_leastpairwise")

        # TODO: exception handling
        if self._players.shape != self._outcomes.shape:
            raise ValueError("interaction.same_shape")

    @property
    def players(self) -> List[Player]:
        return self._players.tolist()

    @property
    def outcomes(self) -> List[GameOutcome]:
        return self._outcomes.tolist()

    def __repr__(self) -> str:
        repr = [
            f"{p}:{o}"
            for p, o in zip(self.players, self.outcomes)
        ]
        repr = ", ".join(repr)
        return f"Interaction({repr})"

    @property
    def order(self) -> int:
        return self._players.shape[-1]

    def as_pairs(self) -> 'List[Interaction]':
        """
           Use this method to converts the current, possibly multiplayer,
           multioutcome interaction into a set of pairwise interactions.

        :raises ValueError: if the order of the current interaction is
            is less than 2.
        :return: a list of pairwise interactions derived from the current
            interaction.
        :rtype: List[Interaction]
        """

        if self.order == 2:
            return [self]

        interactions = []
        for player, opponent in combinations(
            zip(self.players, self.outcomes), 2
        ):
            players, outcomes = zip(player, opponent)
            interactions.append(
                Interaction(players, outcomes)
            )

        return interactions

    def __eq__(self, other: 'Interaction') -> bool:
        return (
            np.array_equal(self._players, other._players) and
            np.array_equal(self._outcomes, other._outcomes)
        )


class History(Generic[GameOutcome]):

    def __init__(
        self, interactions: Iterable[Interaction[GameOutcome]]
    ):
        self._interactions = interactions
        self._population = Population.from_players_interactions(
            interactions
        )

    @property
    def players(self) -> List[Player]:
        """  
           Returns the list of players involved
           in the interactions.

        :return: list of players in the interactions.
        :rtype: List[Player]
        """
        return list(self._population.players)

    def __iter__(self) -> Iterable[Interaction[GameOutcome]]:
        return self._interactions

    @classmethod
    def from_interactions(
        cls,
        interactions: Union[
            Iterable[Interaction[GameOutcome]],
            'History[GameOutcome]'
        ]
    ) -> 'History[GameOutcome]':
        if isinstance(interactions, History):
            return interactions
        elif isinstance(interactions, Iterable):
            return History(interactions)

        raise ValueError()  # TODO: exception raising.


@dataclass
class TimedIntereaction(Interaction[GameOutcome]):
    timestep: int

    def __repr__(self) -> str:
        rep = super().__repr__()
        return f"TimedInteraction(step={self.timestep}, interaction={rep})"


PlayerType = TypeVar("PlayerType", bound=PlayerLike)


class Population(Generic[PlayerType]):
    """
        The Population class implements a storage for any collection
        of players.
    """

    def __init__(
            self, uid: str, players: Iterable[PlayerType]):
        """

        :param uid: Unique identifier for the population.
        :type uid: str
        :param players: List of players that belong to the population.
        :type players: Iterable[Player]
        """

        self.uid = uid
        self._players = dict[str, PlayerType]()
        self._players_idx = dict[int, str]()
        self._size: int = 0
        for player in players:
            self.aggregate(player)

    def aggregate(self, player: PlayerType):
        """
            Adds a player to the population

        :param player: the player to be added to the population.
                        The player identifier should be unique.
        :type player: Player
        """
        assert player.id not in self._players
        self._players[player.id] = player
        self._players_idx[player.id] = self._size
        self._size += 1

    @property
    def players(self) -> np.ndarray[Any, PlayerType]:
        """
            Returns a numpy array with players in the population.

        :return: A numpy array with the players in the population.
        :rtype: np.ndarray[Any, PlayerType]
        """
        return np.array([player for player in self._players.values()])

    @property
    def size(self):
        return self._size

    def __iter__(self):
        return self.players

    def __str__(self) -> str:
        return self.uid

    def __repr__(self) -> str:
        return f"Population(id={self.uid})"

    def __getitem__(self, player_id: str) -> int:
        assert player_id in self._players
        return self._players_idx[player_id]

    def __contains__(self, player: PlayerType) -> bool:
        if isinstance(player, str):
            return player in self._players

        if isinstance(player, Player):
            return player in self.players

        raise ValueError()  # TODO: codify exception

    @classmethod
    def from_players_uid(
        cls, uid: str, players_uid: Iterable[str]
    ) -> 'Population[PlayerType]':
        """
            Constructs a Population object from an iterable of unique
            players identifiers.

        :param uid: Unique identifier for the population.
        :type population_id: str
        :param players: A sequence of players' unique identifiers
        :type players: Iterable[str]
        :return: A population containing a collection of players.
        :rtype: Population
        """
        # TODO: implement exception handling here.
        assert cls == Population, "Do not call from subclasses"

        population = Population[PlayerType](uid)
        for player_id in players_uid:
            population.add(
                Player(player_id)
            )
        return population

    @classmethod
    def from_players_interactions(
        cls, interactions: List[Interaction], uid: Optional[str] = None
    ) -> 'Population':
        """
           Constructs a population of players from a set of interactions.

        :param interactions: _description_
        :type interactions: List[Interaction]
        :return: _description_
        :rtype: Population
        """
        population = Population(uid=uid, players=[])
        for interaction in interactions:
            for player in interaction.players:
                if isinstance(player, str):
                    player = Player(player)
                if player.id not in population:
                    population.aggregate(player)

        return population
