import unittest
from popcore.phylogenetic import PhylogeneticTree
import random


class TestPhylogenetic(unittest.TestCase):

    def mutate(parent_parameters, hyperparameters, contributors=[]):
        new_DNA = list(parent_parameters)
        new_DNA[hyperparameters["spot"]] = hyperparameters["letter"]
        new_DNA = ''.join(new_DNA)
        return new_DNA, hyperparameters

    def test_construction(self):
        # Visual test, uncomment the last line to see what the resulting trees
        # look like and check that they make sense.

        # Suppose this is a tree tracking the evolution of a
        # strand of DNA

        tree = PhylogeneticTree(hyperparameter_names=["letter", "spot"],
                                step_function=TestPhylogenetic.mutate,
                                tree_sparsity=3)
        # tree.add_root("GGTCAACAAATCATAAAGATATTGG")  # Land snail DNA
        new_DNA = "OOOOO"
        tree.add_root(new_DNA)
        tree.add_root(new_DNA)
        tree.add_root(new_DNA)

        for _ in range(64):
            node = tree.nodes[random.choice(list(tree.nodes.keys()))]
            letter = random.choice("ACGT")
            spot = random.randrange(len(new_DNA))

            hyperparameters = {"letter": letter, "spot": spot}
            new_DNA, _ = TestPhylogenetic.mutate(node.get_model_parameters(),
                                                 hyperparameters)

            node.add_child(model_parameters=new_DNA,
                           hyperparameters=hyperparameters)

        tree.draw()

    def test_reconstruction_from_hyperparam(self):
        # Tests that any iteration of the models can be recovered even if it
        # was not saved
        tree = PhylogeneticTree(hyperparameter_names=["letter", "spot"],
                                step_function=TestPhylogenetic.mutate,
                                tree_sparsity=3)
        new_DNA = "OOOOO"
        node = tree.add_root(new_DNA)

        DNA_iterations = [new_DNA]

        # Generate the tree but don't keep the DNA strands
        for _ in range(64):
            letter = random.choice("ACGT")
            spot = random.randrange(len(new_DNA))

            hyperparameters = {"letter": letter, "spot": spot}
            new_DNA, _ = TestPhylogenetic.mutate(new_DNA, hyperparameters)
            DNA_iterations.append(new_DNA)

            node.add_child(hyperparameters=hyperparameters)
            node = node.children[0]

        # Retrieve the DNA strands from the hyperparameters
        retrieved_DNA = []
        node = tree.roots[0]
        retrieved_DNA.append(node.get_model_parameters(save=False))

        while len(node.children) > 0:
            node = node.children[0]
            retrieved_DNA.append(node.get_model_parameters(save=False))

        self.assertListEqual(DNA_iterations, retrieved_DNA)

    def test_undefined_step_function(self):
        tree = PhylogeneticTree(hyperparameter_names=["letter", "spot"])
        new_DNA = "OOOOO"
        node = tree.add_root(new_DNA)
        node.add_child(hyperparameters={"spot": 0, "letter": "A"})

        self.assertRaises(ValueError, node.children[0].get_model_parameters)
