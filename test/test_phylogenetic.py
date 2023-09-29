import unittest
from popcore.phylogenetic import Population
import random

# Display libraries
import networkx as nx                                   # type: ignore
import matplotlib.pyplot as plt                         # type: ignore
from networkx.drawing.nx_pydot import graphviz_layout   # type: ignore


def draw(population: Population) -> None:  # TODO: Move that

    """Displays the phylogenetic tree.

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


class TestPhylogenetic(unittest.TestCase):

    def mutate(parent_parameters, hyperparameters, contributors=[]):
        new_DNA = list(parent_parameters)
        new_DNA[hyperparameters["spot"]] = hyperparameters["letter"]
        new_DNA = ''.join(new_DNA)
        return new_DNA, hyperparameters

    def test_visual_construction(self):
        # Visual test, uncomment the last line to see what the resulting trees
        # look like and check that they make sense.

        # Suppose this is a tree tracking the evolution of a
        # strand of DNA

        pop = Population(sparsity=0)
        # tree.add_root("GGTCAACAAATCATAAAGATATTGG")  # Land snail DNA
        new_DNA = "OOOOO"
        pop.branch("Lineage 1")
        pop.branch("Lineage 2")
        pop.branch("Lineage 3")

        pop.checkout("Lineage 1")
        pop.commit(model_parameters=new_DNA)

        pop.checkout("Lineage 2")
        pop.commit(model_parameters=new_DNA)

        pop.checkout("Lineage 3")
        pop.commit(model_parameters=new_DNA)

        for _ in range(32):
            branch = random.choice(list(pop.branches.keys()))

            if branch == "_root":
                continue

            letter = random.choice("ACGT")
            spot = random.randrange(len(new_DNA))

            pop.checkout(branch)

            hyperparameters = {"letter": letter, "spot": spot}
            new_DNA, _ = TestPhylogenetic.mutate(pop.get_model_parameters(),
                                                 hyperparameters)

            pop.commit(model_parameters=new_DNA,
                       hyperparameters=hyperparameters)

        # draw(pop)

    def test_linear(self):
        pop = Population(sparsity=0)

        new_DNA = "OOOOO"
        DNA_history = [new_DNA]

        pop.commit(model_parameters=new_DNA)

        for x in range(16):
            letter = random.choice("ACGT")
            spot = random.randrange(len(new_DNA))

            hyperparameters = {"letter": letter, "spot": spot}
            new_DNA, _ = TestPhylogenetic.mutate(new_DNA,
                                                 hyperparameters)
            DNA_history.append(new_DNA)

            pop.commit(model_parameters=new_DNA,
                       hyperparameters=hyperparameters)

        # draw(pop)

        nbr_nodes = 1
        node = pop._root
        while len(node.children):
            nbr_nodes += 1
            assert len(node.children) == 1
            node = node.children[0]
            assert node.model_parameters == DNA_history[nbr_nodes-2]

        assert nbr_nodes == 18

    def test_sparsity(self):
        pop = Population(sparsity=3)

        new_DNA = "OOOOO"
        DNA_history = [new_DNA]

        pop.commit(model_parameters=new_DNA)

        for x in range(16):
            letter = random.choice("ACGT")
            spot = random.randrange(len(new_DNA))

            hyperparameters = {"letter": letter, "spot": spot}
            new_DNA, _ = TestPhylogenetic.mutate(new_DNA,
                                                 hyperparameters)
            DNA_history.append(new_DNA)

            pop.commit(model_parameters=new_DNA,
                       hyperparameters=hyperparameters)

        # draw(pop)

        nbr_nodes = 1
        node = pop._root
        while len(node.children):
            nbr_nodes += 1
            self.assertEqual(len(node.children), 1)
            node = node.children[0]
            if (nbr_nodes - 2) % 4 == 0:
                self.assertEqual(node.model_parameters,
                                 DNA_history[nbr_nodes-2])
            else:
                self.assertIsNone(node.model_parameters)

        assert nbr_nodes == 18
