# PopCore
Core Library of PopRL

# TODO: Release 1.0.0
- [X] Clean up main dir
- [X] Divide features into Implemented and Future
- [X] Write documentation/example of phylogenetic tree.
- [X] Check requirements
- [X] Switch to TOML
- [X] Licence: MIT
- [ ] Upload to PyPi

# Features

### Implemented

- Population of agents as a git-like data structure
    - Commits
    - Branching
    - Iterators through elements of the population
    - Thread-safe attach/detach operations for multiprocessing
    
- Interactions

### Future

- Saving/Loading populations
- pop.fork/pop.merge

# Documentation

## popcore.core.Interaction

**class popcore.core.Interaction(players: List[Player], outcomes: List[OUTCOME], timestep: int = 0)**

An interaction between an arbitrary number of Players.

**Parameters:**
- **players (List[Player]):**

    A list of the players involved in the interaction

- **outcomes (List[OUTCOME]):**

    The outcomes of the interaction. There must be one outcome per player.

- **timestep (int) = 0:**

    The timestep at which the interaction occured.


**Attributes:**

- **players (List[Player]):**

    A list of the players involved in the interaction

- **outcomes (List[OUTCOME]):**

    The outcomes of the interaction.

- **timestep (int) = 0:**

    The timestep at which the interaction occured.

## popcore.population.Player

**class popcore.population.Player(parent: 'Player | None' = None, model_parameters: Any = None, id_str: str = '', hyperparameters: Dict[str, Any] | None = None, contributors: 'List[Player] | None' = None, generation: int = 0, timestep: int = 1, branch_name: str = '')**

A specific version of an agent at a given point in time. This is equivalent to a commit in the population.

**Parameters:**
- **parent (Player | None):** 

    The parent of this player.
    If None, this is considered a root. Every player may only have one parent, but if it needs more, it can have arbitrarily many contributors. Defaults to None

- **model_parameters (Any):**

    The parameters of the model. With
    neural networks, that would be the weights and biases.
    Defaults to None.

- **id_str (str):**
    
    The id_str of the player to find it in a population.
    id_strs must be unique within each pop. Defaults to the empty string.

- **hyperparameters (Dict[str, Any]):**

    A dictionary of the hyperparameters that define the transition from the parent to this player. This should contain enough information to reproduce the evolution step deterministically given the
    parent and contributors parameters.
    Defaults to an empty dict.

- **contributors (List[PhylogeneticTree.Node]):**

    All the models
    other than the parent that contributed to the evolution.
    Typically, that would be opponents and allies, or mates in
    the case of genetic crossover.
    For example, if the model played a game of chess against
    an opponent and learned from it, the parent would be the
    model before that game, and the contributor would be the
    opponent. Defaults to an empty list.
            
- **generation (int):**

    The generation this player belongs to.
    Defaults to 1.

- **timestep (int):**

    The timestep when this player was created.
    Defaults to 1.

**Attributes**

- **parent (Player | None):** 

    The parent of this player.

- **model_parameters (Any):**

    The parameters of the model. With neural networks, that would be the weights and biases.

- **id_str (str):**
    
    The id_str of the player to find it in a population.

- **hyperparameters (Dict[str, Any]):**

    A dictionary of the hyperparameters that define the transition from the parent to this player.

- **contributors (List[PhylogeneticTree.Node]):**

    All the models other than the parent that contributed to the evolution.
    Typically, that would be opponents and allies, or mates in
    the case of genetic crossover.
    For example, if the model played a game of chess against
    an opponent and learned from it, the parent would be the
    model before that game, and the contributor would be the
    opponent.
            
- **generation (int):**

    The generation this player belongs to.

- **timestep (int):**

    The timestep when this player was created.

**Methods**
- [popcore.population.Player.has_child](#popcorepopulationplayerhas_child)
- [popcore.population.Player.add_child](#popcorepopulationplayeradd_child)
- [popcore.population.Player.load_model_parameters](#popcorepopulationplayerload_model_parameters)

**See also** 
- [popcore.population.Population](#popcorepopulationpopulation)


## popcore.population.Player.add_child

**popcore.population.Player.add_child(model_parameters=None, id_str: str = '', hyperparameters: Dict[str, Any] | None = None, contributors: 'List[Player] | None' = None, new_generation: bool = True, timestep: int = 1, branch_name: str = '') -> popcore.population.Player**

Adds a child to this node.

If `node` is directly specified then it will be added as a child.
Otherwise, the other parameters will be used to create a new node
and add it as a child.

**Args:**
- **model_parameters (Any):**

    The model parameters of the child to be added. Defaults to `None`.

- **id_str (str):**

    The id_str of the child. If this is the empty string, a unique id_str will be picked at random.
    Defaults to the empty string.
    
- **hyperparameters (Dict[str, Any]):**

    A dictionary of the
    hyperparameters that define the transition from this node
    to the new child. This should contain enough information to
    reproduce the evolution step deterministically given the
    parent and contributors parameters.
    Defaults to an empty dict.

- **contributors (List[PhylogeneticTree.Node]):**

    All the models
    other than the parent that contributed to the evolution.
    Typically, that would be opponents and allies, or mates in
    the case of genetic crossover.
    For example, if the model played a game of chess against
    an opponent and learned from it, the parent would be the
    model before that game, and the contributor would be the
    opponent. Defaults to an empty list.

- **new_generation: bool = True:**

    If set to `True`, the child's generation will be the current node's generation + 1. If set to false, it will be the current node's generation. Defaults to `True`

- **timestep: int = 1:**

    The timestep at which this child was created. Defaults to `1`.

- **branch_name: str = '':**

    The name of the branch this child belongs to. Defaults to the empty string.

**Returns:**
- **popcore.population.Player:**
    
    The new child

**Raises:**
- **ValueError:**

    If the id_str conflicts with an other node in the tree.

**See also**
- [popcore.population.Player](#popcorepopulationplayer)
- [popcore.population.Player.has_child](#popcorepopulationplayerhas_child)



## popcore.population.Player.has_child

**popcore.population.Player.has_child() -> bool**

Returns True if the Player has at least one child.

**Returns:**
- **bool:**
    
    True if the Player has at least one child. Otherwise False.

**See also**
- [popcore.population.Player](#popcorepopulationplayer)
- [popcore.population.Player.add_child](#popcorepopulationplayeradd_child)

## popcore.population.Player.load_model_parameters

**popcore.population.Player.load_model_parameters(load_hook: Callable[[str], Any])**

Calls the load_hook function with `self.id_str` as argument.

**Args:**
- **load_hook: Callable[[str], Any]:**

    A function that takes the id_str of the player as argument and returns the model that corresponds.

**Returns:**
- **Any:**

    The return value of `load_hook`

**See also**
- [popcore.population.Player](#popcorepopulationplayer)


## popcore.population.Population

**class popcore.population.Population(root_id: str = "_root")**

Instantiates population of agents.

This is a data structure that records the evolution of populations of
agents. It behaves like a git repository, where each branch is a
unique agent and every commit corresponds to a specific iteration of
said agent.

This is initialized with a '_root' branch. Users should not commit
directly to this branch if they want to track multiple separate agents,
but rather create a branch for every new agent.

**Args:**
- **root_id (str) = "_root":**

    The id of the root of the population (where the root is an initial empty commit). Defaults to `"_root"`.

**Attributes**

- **nodes: Dict[str, Player]**

    A dictionary with all `id_str : Player` pairs in the population. Note that `id_str` can be either the ID of a commit or the name of a branch.

- **generations: List[List[Player]]**

    A list of Players in the population indexed by generation

- **current_node: Player**

    The current commit

- **current_branch: str**

    The current branch

- **branches: Set[str]**

    The set of all branch names

**Methods**

- [popcore.population.Population.commit](#popcorepopulationpopulationcommit)
- [popcore.population.Population.branch](#popcorepopulationpopulationbranch)
- [popcore.population.Population.checkout](#popcorepopulationpopulationcheckout)
- [popcore.population.Population.get_model_parameters](#popcorepopulationpopulationget_model_parameters)
- [popcore.population.Population.walk_lineage](#popcorepopulationpopulationwalk_lineage)
- [popcore.population.Population.walk_gen](#popcorepopulationpopulationwalk_gen)
- [popcore.population.Population.walk](#popcorepopulationpopulationwalk)
- [popcore.population.Population.get_branches](#popcorepopulationpopulationget_branches)
- [popcore.population.Population.get_current_branch](#popcorepopulationpopulationget_current_branch)
- [popcore.population.Population.detach](#popcorepopulationpopulationdetach)
- [popcore.population.Population.attach](#popcorepopulationpopulationattach)


**See also**
- [popcore.population.Player](#popcorepopulationplayer)

## popcore.population.Population.commit

**popcore.population.Population.commit(model_parameters: Any = None, hyperparameters: Dict[str, Any] | None = None, contributors: 'List[Player] | None' = None, id_str: str = '', timestep: int = 1, id_hook: Callable[[str], str] = lambda x: x, player_hook: Callable[[Player], Player] = lambda x: x, persist_hook: Callable[[str, Player], None] = lambda x, y: None) -> str**

Creates a new commit in the current branch.

**Args:**
- **model_parameters (Any):**

    The parameters of the model to commit.
    Defaults to None
    
- **hyperparameters (Dict[str, Any]):**

    The hyperparameters to commit.
    Defaults to an empty dict.
    
- **contributors (List[Player]):**

    The agents other than the parent that
    contributed to the last training step (opponents, allies,
    mates...). Defaults to an empty list.
    
- **id_str (str):**

    A unique identifier for the commit (like the commit
    hash in git). If this is the empty string, an id_str will be
    generated using sha1. This value must be unique in the
    Population to uniquely identify each commit. Defaults to the
    empty string

- **timestep: int = 1:**

    The timestep at which this child was created. Defaults to `1`.
    
- **id_hook (Callable[[str], str]):**

    A function that takes id_str if
    provided, or the automatically generated hash if not, and
    returns a new id_str. This will be the hash of the commit,
    hence the result must be unique. This is meant to allow user
    to customize population indexing. Defaults to the identity
    function.
    
- **player_hook (Callable[[Player], Player]):**

    A function that takes
    the newly created Player object and returns a new one to be
    added to the population instead. This is meant to allow users
    to customize player creation. Defaults to the identity
    function.

- **persist_hook (Callable[[str, Player], Player]):**

    A function that
    takes the commit id_str and newly created Player object to
    save the corresponding model. This is meant to allow users
    to save any model they may be using. If it is provided, it
    will be called, so only give this argument if you want that
    specific version of the model to persist. Defaults to the None
    function.

**Raises:**
- **ValueError:**

    If a commit with the specified id_str already exists

**Returns:**
- **str:**
    The id_str of the new commit.

**See also**
- [popcore.population.Player](#popcorepopulationplayer)
- [popcore.population.Population.branch](#popcorepopulationpopulation.branch)
- [popcore.population.Population.checkout](#popcorepopulationpopulationcheckout)
- [popcore.population.Population.walk_lineage](#popcorepopulationpopulationwalk_lineage)
- [popcore.population.Population.walk_gen](#popcorepopulationpopulationwalk_gen)
- [popcore.population.Population.walk](#popcorepopulationpopulationwalk)

## popcore.population.Population.branch

**popcore.population.Population.branch(branch_name: str, auto_rename: bool = False) -> str**

Create a new branch diverging from the current branch.

**Args:**
- **branch_name (str):**

    The name of the new branch. Must be unique.
    This will be a new alias to the current commit

- **auto_rename (bool):**

    If True, a number will be appended to the
    branch name in case of conflict to automatically resolve it.
    Defaults to False.

**Raises:**
- **ValueError:**

    If a commit or branch with the specified branch_name already exists

**Returns:**
- **str:**

    The branch_name of the new branch

**See also**
- [popcore.population.Population.commit](#popcorepopulationpopulationcommit)
- [popcore.population.Population.checkout](#popcorepopulationpopulationcheckout)
- [popcore.population.Population.walk_lineage](#popcorepopulationpopulationwalk_lineage)
- [popcore.population.Population.get_branches](#popcorepopulationpopulationget_branches)
- [popcore.population.Population.get_current_branch](#popcorepopulationpopulationget_current_branch)

## popcore.population.Population.checkout

**popcore.population.Population.checkout(branch_name: str) -> None**

Set the current branch to the one specified.

**Args:**
- **branch_name (str):**

    The name of the branch to switch to.

**Raises:**
- **KeyError:**

    If there is no branch with the specified name

**See also**
- [popcore.population.Population.commit](#popcorepopulationpopulationcommit)
- [popcore.population.Population.branch](#popcorepopulationpopulationbranch)
- [popcore.population.Population.get_branches](#popcorepopulationpopulationget_branches)
- [popcore.population.Population.get_current_branch](#popcorepopulationpopulationget_current_branch)

## popcore.population.Population.get_model_parameters

**popcore.population.Population.get_model_parameters() -> None**

Return the model parameters in the last commit of the current branch

**Returns:**
- **Any:**

    The model parameters in the last commit of the current branch

**See also**
- [popcore.population.Population.commit](#popcorepopulationpopulationcommit)

## popcore.population.Population.walk_lineage

**popcore.population.Population.walk_lineage(branch: str = "") -> Iterator[Player]**

Returns an iterator over the commits in the given branch.

If branch is not specified, it will return an iterator over the current branch.

The list returned is in reverse chronological order, so the most
recent commit appears first, and the oldest last.

**Args:**
- **branch (str):**

    The branch we want to iterate over.

**Returns:**
- **Iterator[Player]:**

    An iterator over the commits in the given branch.

**Raises:**
- **KeyError:** 

    If the specified branch does not exist

**See also**
- [popcore.population.Player](#popcorepopulationplayer)
- [popcore.population.Population.commit](#popcorepopulationpopulationcommit)
- [popcore.population.Population.branch](#popcorepopulationpopulationbranch)
- [popcore.population.Population.walk_gen](#popcorepopulationpopulationwalk_gen)
- [popcore.population.Population.walk](#popcorepopulationpopulationwalk)

## popcore.population.Population.walk_gen

**popcore.population.Population.walk_gen(gen: int = -1) -> Iterator[Player]**

Returns an iterator over the commits in the given generation.

**Args:**
- **gen (int) = 1:**

    The generation to iterate over.

**Returns:**
- **Iterator[Player]:**

    An iterator over the commits in the given generation.

**See also**
- [popcore.population.Player](#popcorepopulationplayer)
- [popcore.population.Population.walk_lineage](#popcorepopulationpopulationwalk_lineage)
- [popcore.population.Population.walk](#popcorepopulationpopulationwalk)


## popcore.population.Population.walk

**popcore.population.Population.walk() -> Iterator[Player]**

Returns an iterator with all the commits in the population

**Returns:**
- **Iterator[Player]:**

    An iterator with all the commits in the population

**See also**
- [popcore.population.Player](#popcorepopulationplayer)
- [popcore.population.Population.commit](#popcorepopulationpopulationcommit)
- [popcore.population.Population.walk_lineage](#popcorepopulationpopulationwalk_lineage)
- [popcore.population.Population.walk_gen](#popcorepopulationpopulationwalk_gen)

## popcore.population.Population.get_branches

**popcore.population.Population.get_branches() -> Set(str)**

Return a set of all branches

**Returns:**
- **Set(str):**

    A set of all branch names.

**See also**
- [popcore.population.Population.branch](#popcorepopulationpopulationbranch)
- [popcore.population.Population.checkout](#popcorepopulationpopulationcheckout)
- [popcore.population.Population.walk_lineage](#popcorepopulationpopulationwalk_lineage)
- [popcore.population.Population.get_current_branch](#popcorepopulationpopulationget_current_branch)

## popcore.population.Population.get_current_branch

**popcore.population.Population.get_current_branch() -> str**

Return the branch you currently are on.

**Returns:**
- **str:**

    The branch you currently are on

**See also**
- [popcore.population.Population.branch](#popcorepopulationpopulationbranch)
- [popcore.population.Population.checkout](#popcorepopulationpopulationcheckout)
- [popcore.population.Population.walk_lineage](#popcorepopulationpopulationwalk_lineage)
- [popcore.population.Population.get_branches](#popcorepopulationpopulationget_branches)

## popcore.population.Population.detach

**popcore.population.Population.detach() -> Population**

Creates a Population with the current commit's id_str as root_id.

The new Population does not have any connection to the current one,
hence this should be thread-safe. This may then be reattached once
operations have been performed.

**Returns:**
- **Population:**

    A new population with the current commit's id_str as root_id.

**See also**
- [popcore.population.Population.attach](#popcorepopulationpopulationattach)

## popcore.population.Population.attach

**popcore.population.Population.attach(population: 'Population', id_hook: Callable[[str], str] = lambda x: x, auto_rehash: bool = False) -> None**

Merges back a previously detached population.

Colliding branch names will have a number appended to fix the
collision. Since commit id_str may collide, new hashes are made by
default. The user may also provide an id_hook to control the way
rehashing happens.

Note that this function preforms changes on both populations involved
in the operation, and that if one wishes to keep versions of these
untouched, they should make a deepcopy beforehand.

Warning: If a model is saved in a detached pop, and the pop is then
reattached, the re-hashing of the commits might make the model not
oadable anymore since the id_str changed (so in case either id_hook
is provided ot auto_rehash is true)

**Args:**
- **population (Population):** 

    The population to merge in the current
    object. It's root's id_str should correspond to the id_str of
    an already existing node, which is where it will be attached.

- **id_hook (Callable[[str], str]):** 

    A function that takes the current
    id_str of every commit in population and returns a new id_str
    to be used when attaching. Note that if auto_rehash is set to
    true, it happens before id_hook is called, hence the new
    hashes is what this function will receive as argument.
    Defaults to the identity function.

- **auto_rehash (bool):** 

    If set to true, re-generates an id_str for every commit before attaching.

**Raises:**
- **ValueError:**

    If the population's root's id_str does not match any current commit.
    
- **ValueError:**

     If there is a collision between commit id_str.
    
**See also**
- [popcore.population.Population](#popcorepopulationpopulation)
- [popcore.population.Population.detach](#popcorepopulationpopulationdetach)


# Examples


This first example shows how to manipulate a population (here, a population of integers since the commits all contain integer values).


```python
"""This tests the correctness of the detach/attach operations"""
pop = Population()  #Initialize the population
pop.branch("b1")    # Create a new branch b1
pop.branch("b2")    # Create a new branch b2
pop.checkout("b1")  # Move to branch b1
a = pop.commit(1)   # Make a commit to branch b1 containing '1'. Save the id_str of the commit in variable 'a'
pop.commit(2)       # Make a new commit containing '2'. This commit is a child of the previous one.
pop.checkout(a)     # Move back to the first commit
pop.commit(3)       # Make a new commit containing '3'. This commit is a child of the commit containing 1 and a sibling of the commit containing '2'.
pop.checkout("_root")# Move back to the _root commit.
pop.branch("b3")    # Create a new branch b3
pop.checkout('b2')  # Move to branch b2
pop.commit(4)       # Make a commit containing '4'
pop.commit(5)       # Make a commut containing '5'. Child of commit 4.
pop.commit(6)       # Make a commit containing '6'. Child of commit 5.
pop.branch("b4")    # Make a new branch b4.
pop.commit(7)       # Make a commit containing '7'. Child of commit 6, still in branch b2
pop.checkout("b4")  # Move to branch b4
pop.commit(8)       # Make a commit containing '8'.
pop.checkout("b3")  # Move to branch b3
a = pop.commit(9)   # Make a commit containing 9. Save the id_str in variable a.
b = pop.commit(15)  # Make a commit containing 15. Save the id_str in variable b.
pop.checkout(a)     # Move back to commit a (containing 9)

pop2 = pop.detach() # Create a new (empty) population pop2 with id_root = a
pop2.branch("b1")   # Create a branch b1. Note: Since this is a separate population from pop, there is no name conflict.
pop2.checkout("b1") # Move to branch b1
c = pop2.commit(10) # Make a commit containing '10'. Save the id_str in variable c.
pop2.commit(11)     # Make a commit containing '11'. Child of commit 10.
pop2.branch("b3")   # Create branch b3
pop2.commit(12)     # Make a commit containing '12'. Child of commit 11, still in branch b1.
pop2.checkout("b3") # Move to branch b3.
pop2.commit(13)     # Make commit containing '13'.
pop2.checkout(pop2._root.id_str)    # Move to the root of pop2
d = pop2.commit(14) # Make a commit containing '14'

self.assertEqual(len(pop2.branches), 3)
self.assertEqual(len(pop2.nodes), 8)    # Note: branches create key-value pairs in pop2.nodes so they add to the node count.

self.assertEqual(len(pop.branches), 5)
self.assertEqual(len(pop.nodes), 15)    # Note: branches create key-value pairs in pop.nodes so they add to the node count.

pop.attach(pop2, auto_rehash=False) # Re-attach the pop2 at the point where it was detached.

self.assertEqual(len(pop.branches), 8)
self.assertEqual(len(pop.nodes), 22)    # Note: branches create key-value pairs in pop.nodes so they add to the node count.

pop.checkout(a)
self.assertListEqual(
    [x.id_str for x in pop.current_node.children], [b, c, d])
```


This second example shows how [popcore.population.Population](#popcorepopulationpopulation) would be used in the case of a tournament where each round, the worst player is replaced by a copy of the best player.


```python
import axelrod as axl   # type: ignore

import unittest
from popcore.population import Population

# Display libraries
import networkx as nx                                   # type: ignore
import matplotlib.pyplot as plt                         # type: ignore
from networkx.drawing.nx_pydot import graphviz_layout   # type: ignore


def draw(population: Population) -> None:

    """Displays the population

    Only parental edges are shown, contributors are ignored."""

    G = nx.Graph()
    G.add_nodes_from(population.nodes.keys())

    queue = [population._root]

    while len(queue):
        node = queue[0]
        queue = queue[1:]

        for c in node.children:
            G.add_edge(node.id_str, c.id_str)
            queue.append(c)

    pos = graphviz_layout(G, prog="dot")
    nx.draw_networkx(G, pos, labels={x.id_str: x.model_parameters
                                     for x in population.nodes.values()})
    plt.show()


def test_axelrod(self):
    """Example of usage of Population with axelrod"""

    # Initialize the population
    pop = Population()
    players = [axl.Cooperator(),
                axl.Defector(),
                axl.TitForTat(),
                axl.Grudger(),
                axl.Alternator(),
                axl.Aggravater(),
                axl.Adaptive(),
                axl.AlternatorHunter(),
                axl.ArrogantQLearner(),
                axl.Bully()]

    # Create a branch for each player
    branches = [pop.branch(str(p), auto_rename=True) for p in players]

    # Commit each player to it's respective branch
    for p, b in zip(players, branches):
        pop.checkout(b)
        pop.commit(p)

    # 7 generations of replacing the worst player by a copy of the best
    for x in range(7):
        # Run a tournament
        tournament = axl.Tournament(players)
        results = tournament.play()

        # Get the best and worst performing agents
        first = results.ranking[0]
        last = results.ranking[-1]

        # Replace the worst player by a copy of the best
        pop.checkout(branches[first])
        branches[last] = pop.branch(str(players[first]), auto_rename=True)

        players[last] = players[first]

        # Commit each player of the new generation to it's respective branch
        for p, b in zip(players, branches):
            pop.checkout(b)
            pop.commit(p)

    # Display the resulting tree visually
    draw(pop)
```