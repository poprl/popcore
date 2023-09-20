from typing import List, Dict, Any
import string
import random
import networkx as nx
import matplotlib.pyplot as plt


class PhylogeneticTree:

    class Node:
        def __init__(self, tree: 'PhylogeneticTree',
                     parent: 'PhylogeneticTree.Node | None' = None,
                     model_parameters=None,
                     ID: str = '',
                     hyperparameters: Dict[str, Any] = {},
                     opponent: 'PhylogeneticTree.Node | None' = None,
                     generation: int = 1,
                     timestep: int = 1):

            self.tree = tree    # The phylogenetic tree this node belongs to
            self.parent = parent
            self.children: List[PhylogeneticTree.Node] = []
            self.model_parameters = model_parameters
            self.set_ID(ID)
            self.generation: int = generation
            self.timestep: int = timestep

            # Parameters to reproduce evolution from parent

            self.hyperparameters: Dict[str, Any] = hyperparameters
            self.opponent: PhylogeneticTree.Node | None = opponent
            # TODO: Allow arbitrarily many opponent/ally teams

            # Check every hyperparameter is defined
            if parent is not None:
                for h in self.tree.hyperparameter_list:
                    if h not in self.hyperparameters.keys():
                        raise KeyError(f"The `{h}` hyperparameter was "
                                       "expected but not found")

            if len(tree.generations) < generation:
                tree.generations.append([])
            tree.generations[generation - 1].append(self)

        def set_ID(self, ID):
            if ID in self.tree.nodes.keys():
                raise ValueError("A node with this ID already exists. "
                                 "Every node must have unique ID")

            # Generate random unique ID
            self.ID = ID
            if self.ID == '':
                while self.ID == '' or ID in self.tree.nodes.keys():
                    self.ID = ''.join(
                        random.choice(string.ascii_letters + string.digits)
                        for i in range(32))

        def set_tree(self, tree: 'PhylogeneticTree'):
            self.tree = tree
            if self.ID in self.tree.nodes.keys():
                self.set_ID('')
            self.tree.nodes[self.ID] = self
            for c in self.children:
                c.set_tree(tree)

        def add_child(self, model_parameters=None,
                      node: 'PhylogeneticTree.Node | None' = None,
                      ID: str = '',
                      hyperparameters: Dict[str, Any] = {},
                      opponent: 'PhylogeneticTree.Node | None' = None):
            """Adds a child to this node

            If `node` is directly specified then it will be added as a child.
            Otherwise, the other parameters will be used to create a new node
            and add it as a child.
            """

            if node is None:
                child = PhylogeneticTree.Node(
                    self.tree, self,
                    model_parameters=model_parameters,
                    ID=ID,
                    hyperparameters=hyperparameters,
                    opponent=opponent,
                    generation=self.generation+1)
            else:
                child = node
                child.parent = self
                child.model_parameters = model_parameters
                child.set_tree(self.tree)
                child.ID = child.set_ID(ID)
                child.generation = self.generation + 1

            self.children.append(child)
            self.tree.nodes[child.ID] = child

        def get_branch_width(self):
            if self.children == []:
                return 1
            return sum([c.get_branch_width() for c in self.children])

    def __init__(self, roots: 'List[PhylogeneticTree.Node]' = [],
                 hyperparameters: list[str] = []):
        # Hyperparameters is the list of all values that need to be tracked to
        # get back to any given generation.

        # The list of 'roots', i.e. models without ancestors
        self.roots: List[PhylogeneticTree.Node] = []
        self.hyperparameter_list = hyperparameters

        # A dictionary containing all nodes in the tree
        self.nodes: Dict[str, PhylogeneticTree.Node] =\
            {root.ID: root for root in self.roots}

        self.generations = []

    def add_root(self, model_parameters, ID: str = ''):
        """Add a root to the tree (A node without ancestors)"""

        root = PhylogeneticTree.Node(tree=self,
                                     model_parameters=model_parameters,
                                     ID=ID)
        self.roots.append(root)
        self.nodes[root.ID] = root

    def draw(self):
        G = nx.Graph()
        G.add_nodes_from(self.nodes.keys())

        queue = self.roots

        while len(queue):
            node = queue[0]
            queue = queue[1:]

            for c in node.children:
                G.add_edge(node.ID, c.ID)
                queue.append(c)

        nx.draw_networkx(G, labels={x.ID: x.model_parameters
                                    for x in self.nodes.values()})
        plt.show()
