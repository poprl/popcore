from dataclasses import dataclass
import os
from typing import Dict, List, Optional
from itertools import chain

from .errors import (
    POPULATION_COMMIT_EXIST, POPUPLATION_BRANCH_EXISTS,
    POPULATION_PLAYER_NOT_EXIST
)
from .core import Interaction, Player
from .hooks import (
    AutoIdHook, PreCommitHook, PostCommitHook, AttachHook,
    ReIdHook, StorageHook
)
from .storage.repo import Repository


class Population:
    """A data structure to manipulate evolving populations of agents.
    The structure is meant to be similar to that of a git repository, where
    every commit corresponds to an agent."""

    def __init__(
        self,
        root: 'Optional[Player]' = None,
        root_name: str = "_root",
        root_branch: str = "main",
        store: 'Optional[Repository]' = None,
        pre_commit_hooks: Optional[List[PreCommitHook]] = None,
        post_commit_hooks: Optional[List[PostCommitHook]] = None,
        attach_hooks: Optional[List[AttachHook]] = None,
    ):
        """Instantiates population of players.

        This is a data structure that records the evolution of populations of
        agents. It behaves like a git repository, where each branch is a
        unique agent and every commit corresponds to a specific iteration of
        said agent.

        This is initialized with a '_root' branch. Users should not commit
        directly to this branch if they want to track multiple separate agents,
        but rather create a branch for every new agent.
        """

        root = root if root else Player(
            parent=None, name=root_name, branch=root_branch
        )
        self._root = root

        # Need to separate root.name and rootbranch otherwise if a commit is
        # made to _root, it updates the _root branch to point at the new commit
        # and we lose the access to the root commit.
        # A dictionary containing all commits in the tree
        # Multiple keys may refer to the same commit. In particular, branches
        # are aliases to specific commits
        # self._nodes: Dict[str, Player] = {
        #     root_name: self._root,
        #     root_branch: self._root
        # }

        self.repo = Repository() if not store else store
        self.repo[root_name, self._root]
        self.repo.branch(root_branch, self._root)

        # An array of every node indexed by generation (1st gen has index 0)
        # self._generations: List[List[Player]] = [[]]

        self._player: Player = self._root
        self._branch: str = self._root.branch

        # Pre-Commit Hooks
        self._pre_commit_hooks: List[PreCommitHook] = [
            AutoIdHook()
        ]
        self._pre_commit_hooks += pre_commit_hooks if pre_commit_hooks else []
        # Post-Commit Hooks
        self._post_commit_hooks: List[PostCommitHook] = [
            StorageHook()
        ]
        self._post_commit_hooks += post_commit_hooks if post_commit_hooks else []
        # Attach Hooks
        self._attach_hooks: List[AttachHook] = [
            ReIdHook()
        ]
        self._attach_hooks += attach_hooks if attach_hooks else []

    def commit(
        self,
        name: str = None,
        interaction: "Interaction | None" = None,
        timestep: int = 1,
        pre_commit_hooks: List[PreCommitHook] | None = None,
        post_commit_hooks: List[PostCommitHook] | None = None,
        **kwargs
    ) -> str:
        """Creates a new commit in the current branch.

        Args: TODO:
            parameters (Any): The parameters of the model to commit.
                Defaults to None
            hyperparameters (Dict[str, Any]): The hyperparameters to commit.
                Defaults to an empty dict.
            interaction (Interaction): The agents other than the parent that
                contributed to the last training step (opponents, allies,
                mates...). Defaults to an empty list.
            name (str): A unique identifier for the commit (like the commit
                hash in git). If this is None, an unique name will be
                generated using cryptographic hashing. Defaults to None
            pre_commit_hooks (List[PreCommitHooks]):
            post_commit_hooks (List[PostCommitHooks]):

        Raises:
            ValueError: If a player with the specified name already exists

        Returns:
            str: The id_str of the new commit.
        """

        # Create the child node
        next_player = self._player.add_descendant(
            name=name,
            interaction=interaction,
            timestep=timestep,
            branch=self._branch
        )

        pre_commit_hooks = pre_commit_hooks if pre_commit_hooks else []
        for hook in chain(
            self._pre_commit_hooks, pre_commit_hooks
        ):
            hook(self, next_player, **kwargs)

        if self.repo.verify(next_player.name):
            raise ValueError(POPULATION_COMMIT_EXIST.format(name))

        self.repo.commit(next_player.name, next_player)
        self.repo.branch(self._branch, self._player)

        post_commit_hooks = post_commit_hooks if post_commit_hooks else []
        for hook in chain(
            self._post_commit_hooks, post_commit_hooks
        ):
            hook(self, next_player, **kwargs)

        self._player = next_player

        return next_player.name

    def branch(self, name: str = None) -> str:
        """Create a new branch diverging from the current branch.

        Args:
            name (str): The name of the new branch. Must be unique.
                This will be a new alias to the current commit. If None, it
                returns the name of the active branch

        Raises:
            ValueError: If a player with the specified name/alias already
            exists

        Returns:
            str: The name of the new commit"""

        if name is None:
            return self._branch

        if name in self.repo:
            raise ValueError(POPUPLATION_BRANCH_EXISTS.format(name))

        self.repo.branch(name, self._player)

        return name

    def checkout(self, name: str) -> str:
        """Set the current branch to the one specified.

        Args:
            name (str): The name of the branch or player to switch to.

        Raises:
            ValueError: If there is no branch with the specified name"""

        if name not in self.repo:
            raise ValueError(POPULATION_PLAYER_NOT_EXIST.format(name))

        self._player: Player = self.repo[name]

        if name in self._branches:
            self._branch = name
        else:
            self._branch = self._player.branch

        return self._branch

    def branches(self) -> Set[str]:
        """Returns a set of all branches"""
        return self._branches

    def detach(
        self,
    ) -> 'Population':
        """Creates a Population with the current player as root.

        The new Population does not have any connection to the current one,
        hence this should be thread-safe. This may then be reattached once
        operations have been performed.

        Returns:
            Population: A new population with the current player as
            root.
        """
        # TODO: detach persistence
        detached_pop = Population(
            root=self._player,
            pre_commit_hooks=self._pre_commit_hooks,
            post_commit_hooks=self._post_commit_hooks,
            attach_hooks=self._attach_hooks,
        )
        return detached_pop

    def attach(
        self,
        population: 'Population',
        attach_hooks: Optional[List[AttachHook]] = None
    ) -> None:
        """Merges back a previously detached population.

        Colliding branch names will have a number appended to fix the
        collision. Since commit id_str may collide, new hashes are made by
        default. The user may also provide an id_hook to control the way
        rehashing happens.

        Note that this function preforms changes on both populations involved
        in the operation, and that if one wishes to keep versions of these
        untouched, they should make a deepcopy beforehand.

        Args:
            population (Population): The population to merge in the current
                object. It's root's id_str should correspond to the id_str of
                an already existing node, which is where it will be attached.
            id_hook (Callable[[str], str]): A function that takes the current
                id_str of every commit in population and returns a new id_str
                to be used when attaching. Note that if auto_rehash is set to
                true, it happens before id_hook is called, hence the new
                hashes is what this function will receive as argument.
                Defaults to the identity function.
            auto_rehash (bool): If set to true, re-generates an id_str for
                every commit before attaching.

        Raises:
            ValueError: If the population's root's id_str does not match any
                current commit.
            ValueError: If there is a collision between commit id_str.
        """

        # TODO Warning: If a model is saved in a detached pop, and the pop is
        # then reattached, the re-hashing of the commits might make the model
        # not loadable anymore since the name changed

        # TODO: attach persistence
        if population._root.name not in self.repo:
            raise ValueError(POPULATION_PLAYER_NOT_EXIST.format(
                population._root.name))

        # Pick the right place to reattach
        node: Player = self.repo[population._root.name]

        # Transfer all the nodes from the other pop to the right place
        for player in population._root.descendants:
            node.descendants.append(player)
            player.parent = node

        nodes_to_add = {}

        # Rename branches in attached pop to avoid conflicts
        branches_to_add, branch_renaming = self._rename_conflicting_branches(
            population
        )

        attach_hooks = attach_hooks if attach_hooks else []
        for name, player in population.repo.items():
            # Ignore root node
            if name == population._root.name:
                continue

            # Add the renamed branches to the main pop
            if name in population._branches:
                nodes_to_add[branch_renaming[name]] = player
                continue

            # Apply branch renaming
            player.branch = branch_renaming[player.branch]

            player.generation += node.generation

            # Apply hooks
            for hook in chain(
                self._attach_hooks, attach_hooks
            ):
                hook(self, player)

            if name in self._nodes:
                raise ValueError(POPULATION_COMMIT_EXIST.format(name))

            # Add player to the index
            self._nodes[player.name] = player

            self._add_gen(player)

        # Add branches to the index
        self._nodes.update(nodes_to_add)
        self._branches = self._branches.union(branches_to_add)

    def head(self) -> 'Player':
        return self._player

    def _rename_conflicting_branches(self, population: 'Population'):
        """Every branch that generates a conflict gets renamed by adding an
        integer at the end"""

        branches_to_add = set()
        branch_renaming = {}

        for branch in population._branches:
            new_branch = branch
            i = 1
            while self._index.exists(new_branch):
                new_branch = branch + str(i)
                i += 1

            branches_to_add.add(new_branch)
            branch_renaming[branch] = new_branch

        return branches_to_add, branch_renaming
