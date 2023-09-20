import unittest
from popcore.phylogenetic import PhylogeneticTree
import random


class TestPhilogenetic(unittest.TestCase):
    def test_construction(self):
        # Suppose this is a tree tracking the evolution of a
        # strand of DNA

        tree = PhylogeneticTree(hyperparameters=["letter", "spot"])
        # tree.add_root("GGTCAACAAATCATAAAGATATTGG")  # Land snail DNA
        tree.add_root("OOOOO")

        for _ in range(12):
            node = tree.nodes[random.choice(list(tree.nodes.keys()))]
            letter = random.choice("ACGT")
            spot = random.randrange(len(node.model_parameters))

            new_DNA = list(node.model_parameters)
            new_DNA[spot] = letter
            new_DNA = ''.join(new_DNA)

            node.add_child(new_DNA, hyperparameters={"letter": letter,
                                                     "spot": spot})

        # tree.draw()
