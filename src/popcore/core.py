from typing import Generic, List, Optional, TypeVar


GameOutcome = TypeVar("GameOutcome")


class Player:
    """
    A specific version of an agent at a given point in time.

    This is equivalent to a commit in the population.

    :param str id: The id of the player to find it in the population.
            ids must be unique within each population. Defaults to None.
    :param Optional[Player] parent: The parent of this player.
        If None, this is considered a root. Every player may only
        have one parent. Defaults to None
    :param Optional[Interaction] interaction: __description__
    :param Optional[int] generation: The generation this player belongs to.
        Defaults to 0.
    :param Optional[int] timestep: The timestep when this player was
        created. Defaults to 1.

    .. seealso::
        :class:`popcore.core.Team`

        :class:`popcore.core.Interaction`

        :class:`popcore.population.Population`
    """

    def __init__(
        self,
        id: Optional[str] = None,
        parent: 'Optional[Player]' = None,
        interaction: 'Optional[Interaction]' = None,
        generation: Optional[int] = 0,
        timestep: Optional[int] = 1,
        branch: Optional[str] = None,
    ):
        # TODO: Should this raise an error if the id is already taken?
        self.id = id
        self.parent = parent
        self.descendants: List[Player] = []

        self.interaction = interaction

        self.generation: int = generation
        self.timestep: int = timestep

        self.branch = branch

    def add_descendant(
        self,
        id: Optional[str] = None,
        interaction: Optional['Interaction'] = None,
        timestep: Optional[int] = 1,
        branch: Optional[str] = None
    ) -> 'Player':

        """Adds a decendant to this player.

        :param Optional[str] id: The id of the child.
            Defaults to None.
        :param Optional[Interaction] interaction: All the models
            other than the parent that contributed to the evolution.
            Typically, that would be opponents and allies, or mates in
            the case of genetic crossover.
            For example, if the model played a game of chess against
            an opponent and learned from it, the parent would be the
            model before that game, and the contributor would be the
            opponent. Defaults to None.
            TODO: update interaction description.
        :param Optional[int] timestep: The timestep when the descendent was
            created. Defaults to 1.
        :param Optional[str] branch: The branch this descendent belongs to.
            Defaults to None.

        :return: The new descendant
        :rtype: Player

        .. seealso::
            :meth:`popcore.core.Player.has_descendants`
        """

        # TODO: Should this check the branch exists or create it otherwise?

        branch = self.branch if branch is None else branch

        # Create child node
        descendant = Player(
            id=id,
            parent=self,
            interaction=interaction,
            generation=self.generation + 1,
            timestep=timestep,
            branch=branch
        )

        self.descendants.append(descendant)

        return descendant

    def has_descendants(self) -> bool:
        """Returns True if the player has descendants

        .. seealso::
            :meth:`popcore.core.Player.add_descendants`"""
        return len(self.descendants) > 0


class Team(Player):
    """
    A Team is a Player with an additional `members` attribute which is a
    list of (sub)players that make up the team.

    :param str id: The id of the Team. ids must be unique within each
        population.
    :param list[Player] members: The players that constitute the team.

    .. seealso::
        :class:`popcore.core.Player`

        :class:`popcore.population.Population`
    """
    members: "list[Player]"

    def __init__(self, id: str, members: "list[Player]"):
        self.members = members
        super().__init__(id)


class Interaction(Generic[GameOutcome]):
    """A list of the players that took part in an interaction, and their
    individual outcomes.

    :param List[Player] players: Players involved in the game.
    :param Lists[GameOutcome] outcomes: outcomes for each player involved in
        the game.
    :param int timestep: The timestep when the interaction occured. Defaults to
        0.
    """

    def __init__(
        self,
        players: List[Player],
        outcomes: List[GameOutcome],
        timestep: int = 0
    ):
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
