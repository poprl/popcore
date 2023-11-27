from .population import Population
from .iterators import flatten


def draw(population: Population):
    """Displays the phylogenetic tree.

    Only parental edges are shown, contributors are ignored."""

    import networkx as nx                              # type: ignore
    import matplotlib.pyplot as plt                         # type: ignore
    from networkx.drawing.nx_pydot import graphviz_layout   # type: ignore

    graph = nx.Graph()
    graph.add_nodes_from(population._nodes.keys())

    for node in flatten(population):
        graph.add_edge(node.id, node.parent.id)

    pos = graphviz_layout(graph, prog="dot")
    nx.draw_networkx(
        graph,
        pos,
        labels={x.name: x.name for x in population._nodes.values()}
    )
    plt.show()
