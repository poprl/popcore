from dataclasses import dataclass
from typing import Generic, Iterable, List, Optional

from .core import (
    Interaction, Population, PlayerType
)


@dataclass
class Operator:
    """
        operator(player0) -> player1
    """
    id: str


@dataclass
class EvolutionStep(Generic[PlayerType]):
    """
        player0 -- [operator] --> player1
    """
    player: PlayerType
    operator: Operator
    descendant: PlayerType
    step: int
    interaction: Optional[Interaction] = None


class Lineage(Generic[PlayerType], Population[PlayerType]):
    """
       A Population of players related by a sequence of evolutionary steps.
       We consider an evolution step.

       Example
       -------

       A reinforcement learning algorithm L, can be understood as an
       evolutionary operator that given an initial policy/player.
    """

    def __init__(self, uid: str, root: PlayerType):
        super().__init__(uid, [root])
        self._steps: List[EvolutionStep] = []

    def aggregate(
        self, player: PlayerType, operator: Optional[Operator] = None,
        interaction: Optional[Interaction] = None
    ):
        """
            Records the evolutionary step that expands the population.

        :param descendant: Player produced by the evolutionary step.
        :type descendant: PlayerType
        :param operator: Operator that produced the step, defaults to None
        :type operator: Optional[Operator], optional
        :param interaction: An object describing the players involved in
                            the interaction, defaults to None.
        :type interaction: Optional[Interaction], optional
        """
        # TODO: limitation/complication to clearly represent Binary/NAry
        # Operators e.g., A + B = C
        # Example: Curriculum learning L(policy0, env0), L(policy1, env5), ...
        super().aggregate(player)
        self._steps.append(
            EvolutionStep(
                self.head, operator, player,
                step=self.generation, interaction=interaction
            )
        )

    @property
    def generation(self) -> int:
        """
            Returns an integer with the current the length of the lineage.

        :return: _description_
        :rtype: int
        """
        return len(self.players)

    @property
    def head(self) -> PlayerType:
        """
            Returns the last player produced by the evolutionary process.
        """
        return self.players[-1]

    @property
    def tail(self) -> PlayerType:
        """
            Returns the seed (first) player in the evolutionary process.
        """
        return self.players[0]


class EvolutionTree(Generic[PlayerType], Population[PlayerType]):

    def __init__(self, uid: str, default_lineage_uid: str = "_root"):
        super().__init__(uid, [])
        self._lineages = dict[str,  Lineage[PlayerType]]()
        self._lineage: str = default_lineage_uid  # active lineage
        self.lineage(default_lineage_uid)

    def aggregate(
        self, player: PlayerType, operator: Optional[Operator] = None,
        interaction: Optional[Interaction] = None
    ):
        """
            Aggregates a player to the active lineage.

        :param player: _description_
        :type player: Player
        :param operator: _description_, defaults to None
        :type operator: Optional[Operator], optional
        :param interaction: _description_, defaults to None
        :type interaction: Optional[Interaction], optional
        """
        lineage = self._lineages[self._lineage]

        super().aggregate(player)
        lineage.aggregate(
            player, operator, interaction
        )

    def lineage(self, uid: str, create_if_not_exist: bool = True) -> Lineage:
        if uid not in self._lineages:
            if not create_if_not_exist:
                raise ValueError()  # TODO: codify exception

            self._lineages[uid] = Lineage(uid, self.head)

        self._lineage = uid  # sets the active lineage to `uid`
        return self._lineages[uid]

    @property
    def head(self) -> PlayerType:
        """
            Returns the last player produced in the active lineage.
        """
        return self.lineage(self._lineage).head

    @property
    def tail(self) -> PlayerType:
        """
            Returns the seed (first) player produced in the active lineage.
        """
        return self.lineage(self._lineages).tail
