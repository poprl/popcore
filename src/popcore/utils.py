
from typing import List
from . import Population, Player


def draw(population: Population):
    """Displays the phylogenetic tree.

    Only parental edges are shown, contributors are ignored."""

    import networkx as nx                              # type: ignore
    import matplotlib.pyplot as plt                         # type: ignore
    from networkx.drawing.nx_pydot import graphviz_layout   # type: ignore

    graph = nx.Graph()
    graph.add_nodes_from(population.nodes.keys())

    queue: List[Player] = [population._root]

    while len(queue):
        node = queue[0]
        queue = queue[1:]

        for c in node.children:
            graph.add_edge(node.id_str, c.id_str)
            queue.append(c)

    pos = graphviz_layout(graph, prog="dot")
    nx.draw_networkx(
        graph,
        pos,
        labels={x.name: x.name for x in population.nodes.values()}
    )
    plt.show()

