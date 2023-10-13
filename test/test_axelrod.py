import axelrod as axl   # type: ignore

import unittest
from popcore.population import Population

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


class TestAxelrod(unittest.TestCase):

    def test_axelrod(self):

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

        branches = [pop.branch(str(p), auto_rename=True) for p in players]

        for p, b in zip(players, branches):
            pop.checkout(b)
            pop.commit(p)

        for x in range(7):
            tournament = axl.Tournament(players)
            results = tournament.play()

            first = results.ranking[0]
            last = results.ranking[-1]

            pop.checkout(branches[first])
            branches[last] = pop.branch(str(players[first]), auto_rename=True)

            players[last] = players[first]

            for p, b in zip(players, branches):
                pop.checkout(b)
                pop.commit(p)

        # draw(pop)
