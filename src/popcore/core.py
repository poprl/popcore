from dataclasses import dataclass
from typing import Any, Generic, Iterable, List, TypeVar

import numpy as np
import numpy.typing as npt


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

    def has_descendants(self) -> bool:
        return len(self.descendants) > 0


@dataclass
class Team(Player):
    """
       A team is a collection of players that act together.
    """
    members: "list[Player]"


@dataclass
class Interaction(Generic[GameOutcome]):
    """_summary_
        players: players involved in the game
        scores: outcomes for each player involved in the game
    """
    players: List[Player]
    outcomes: List[GameOutcome]

    def __repr__(self) -> str:
        repr = [
            f"{p}:{o}"
            for p, o in zip(self.players, self.outcomes)
        ]
        repr = ", ".join(repr)
        return f"Interaction({repr})"


@dataclass
class TimedIntereaction(Interaction[GameOutcome]):
    timestep: int

    def __repr__(self) -> str:
        rep = super().__repr__()
        return f"TimedInteraction(step={self.timestep}, interaction={rep})"


PlayerType = TypeVar("PlayerType", bound=Player)


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
        self._players = dict[str, Player]()
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

    @property
    def players(self) -> np.ndarray[Any, PlayerType]:
        """
            Returns a numpy array with players in the population.

        :return: A numpy array with the players in the population.
        :rtype: np.ndarray[Any, PlayerType]
        """
        return np.array(self._players.values())

    @property
    def size(self):
        return len(self._players)

    def __iter__(self):
        return self.players

    def __str__(self) -> str:
        return self.uid

    def __repr__(self) -> str:
        return f"Population(id={self.uid})"

    def __contains__(self, player: PlayerType | str) -> bool:
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
        cls, uid: str, interactions: List[Interaction]
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
                if player.id not in population:
                    population.aggregate(player)

        return population
