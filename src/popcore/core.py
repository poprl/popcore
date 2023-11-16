

from typing import Generic, List, Optional, TypeVar


GameOutcome = TypeVar("GameOutcome")


class Player:
    """
        Player
    """
    def __init__(
        self,
        name: Optional[str] = None,
        parent: 'Optional[Player]' = None,
        interaction: 'Optional[Interaction]' = None,
        generation: Optional[int] = 0,
        timestep: Optional[int] = 1,
        branch: Optional[str] = None,
        persistence: Optional[str] = None
    ):

        """A specific version of an agent at a given point in time.

        This is equivalent to a commit in the population.

        Args: TODO
            parent (Player | None): The parent of this player.
                If None, this is considered a root. Every player may only
                have one parent, but if it needs more, it can have
                arbitrarily many contributors. Defaults to None
            model_parameters (Any): The parameters of the model. With
                neural networks, that would be the weights and biases.
                Defaults to None.
            id_str (str): The id_str of the player to find it in the pop.
                id_strs must be unique within each pop. Defaults to the empty
                string.
            hyperparameters (Dict[str, Any]): A dictionary of the
                hyperparameters that define the transition from the parent
                to this player. This should contain enough information to
                reproduce the evolution step deterministically given the
                parent and contributors parameters.
                Defaults to an empty dict.
            contributors (List[PhylogeneticTree.Node]): All the models
                other than the parent that contributed to the evolution.
                Typically, that would be opponents and allies, or mates in
                the case of genetic crossover.
                For example, if the model played a game of chess against
                an opponent and learned from it, the parent would be the
                model before that game, and the contributor would be the
                opponent. Defaults to an empty list.
            generation (int): The generation this player belongs to.
                Defaults to 1.
            timestep (int): The timestep when this player was created.
                Defaults to 1.

        Raises:
            KeyError: If hyperparameters does not contain one of the
                variables that were defined as necessary when creating the
                tree.
            ValueError: If the id_str conflicts with an other node in the tree.
        """
        self.name = name
        self.parent = parent
        self.path: str = ''
        self.descendants: List[Player] = []

        self.interaction = interaction

        self.generation: int = generation
        self.timestep: int = timestep

        self.branch = branch
        self.persistence = persistence

    def add_descendant(
        self,
        name: str = None,
        interaction: 'Interaction' = None,
        timestep: int = 1,
        branch: str = None
    ) -> 'Player':

        """Adds a decendant to this node

        If `node` is directly specified then it will be added as a child.
        Otherwise, the other parameters will be used to create a new node
        and add it as a child.

        Args:
            model_parameters (Any): The model parameters of the child to be
                added. Defaults to None.
            id_str (str): The id_str of the child. If this is the empty string,
                a unique id_str will be picked at random.
                Defaults to the empty string.
            hyperparameters (Dict[str, Any]): A dictionary of the
                hyperparameters that define the transition from this node
                to the new child. This should contain enough information to
                reproduce the evolution step deterministically given the
                parent and contributors parameters.
                Defaults to an empty dict.
            interaction (List[Player]): All the models
                other than the parent that contributed to the evolution.
                Typically, that would be opponents and allies, or mates in
                the case of genetic crossover.
                For example, if the model played a game of chess against
                an opponent and learned from it, the parent would be the
                model before that game, and the contributor would be the
                opponent. Defaults to an empty list.

        Returns:
            Player: The new descendant

        """

        branch = self.branch if branch is None else branch

        # Create child node
        descendant = Player(
            name=name,
            parent=self,
            interaction=interaction,
            generation=self.generation + 1,
            timestep=timestep,
            branch=branch
        )

        self.descendants.append(descendant)

        return descendant

    def has_descendants(self) -> bool:
        return len(self.descendants) > 0


class Team(Player):
    """
       Team
    """
    members: "list[Player]"

    def __init__(self, name: str, members: "list[Player]"):
        self.members = members
        super().__init__(name)


class Interaction(Generic[GameOutcome]):
    """_summary_
        players: players involved in the game
        scores: outcomes for each player involved in the game
    """

    def __init__(
        self,
        players: List[Player],
        outcomes: List[GameOutcome],
        timestep: int = 0
    ):
        """_summary_

        Args:
            players (List[Player]): TODO _description_
            outcomes (List[OUTCOME]): TODO _description_
            timestep (int): TODO: description
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
