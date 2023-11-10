import unittest
from popcore.core import Population, Interaction


class TestCommit(unittest.TestCase):
    def assert_invariants(self, pop):
        """Properties that should be invariant under any commit arguments"""
        self.assertEqual(pop._player.branch, "main")
        self.assertEqual(pop._branch, "main")
        self.assertIsNotNone(pop._player.parent)
        self.assertEqual(pop._player.parent, pop._root)
        self.assertEqual(len(pop._nodes), 3)
        self.assertEqual(pop._branches, set(["main"]))
        self.assertEqual(pop._nodes["main"], pop._player)
        self.assertEqual(pop._nodes["_root"], pop._root)
        self.assertEqual(len(pop._generations), 2)
        self.assertEqual(len(pop._generations[0]), 0)
        self.assertEqual(len(pop._generations[1]), 1)
        self.assertEqual(pop._generations[1][0], pop._player)

    def test_without_arguments(self):
        pop = Population()
        pop.commit()

        self.assertIsNone(pop._player.parameters)
        self.assertIsNone(pop._player.hyperparameters)
        self.assertIsNone(pop._player.interaction)
        self.assertEqual(pop._player.timestep, 1)
        self.assertNotEqual(pop._player.name, '')
        self.assert_invariants(pop)

    def test_with_parameter(self):
        pop = Population()
        pop.commit(parameters="Hmm yes")

        self.assertEqual(pop._player.parameters, "Hmm yes")
        self.assertIsNone(pop._player.hyperparameters)
        self.assertIsNone(pop._player.interaction)
        self.assertEqual(pop._player.timestep, 1)
        self.assertNotEqual(pop._player.name, '')
        self.assert_invariants(pop)

    def test_with_hyperparameter(self):
        pop = Population()
        pop.commit(hyperparameters={"Hmm": "yes"})

        self.assertIsNone(pop._player.parameters)
        self.assertEqual(pop._player.hyperparameters, {"Hmm": "yes"})
        self.assertIsNone(pop._player.interaction)
        self.assertEqual(pop._player.timestep, 1)
        self.assertNotEqual(pop._player.name, '')
        self.assert_invariants(pop)

    def test_with_interaction(self):
        pop = Population()
        interac = Interaction(["p1", "p2"], [1, 0])
        pop.commit(interaction=interac)

        self.assertIsNone(pop._player.parameters)
        self.assertIsNone(pop._player.hyperparameters)
        self.assertEqual(pop._player.interaction, interac)
        self.assertEqual(pop._player.timestep, 1)
        self.assertNotEqual(pop._player.name, '')
        self.assert_invariants(pop)

    def test_with_name(self):
        pop = Population()
        pop.commit(name="Helloo")

        self.assertIsNone(pop._player.parameters)
        self.assertIsNone(pop._player.hyperparameters)
        self.assertIsNone(pop._player.interaction)
        self.assertEqual(pop._player.timestep, 1)
        self.assertEqual(pop._player.name, 'Helloo')
        self.assert_invariants(pop)

    def test_same_name_multiple_times(self):
        pop = Population()
        pop.commit(name="Helloo")
        self.assertRaises(ValueError, pop.commit, name="Helloo")

    def test_illegal_name(self):
        pop = Population()
        self.assertRaises(ValueError, pop.commit, name="_root")

    def test_same_name_as_a_branch(self):
        pop = Population()
        self.assertRaises(ValueError, pop.commit, name="main")

    def test_with_timestep(self):
        pop = Population()
        pop.commit(timestep=2)

        self.assertIsNone(pop._player.parameters)
        self.assertIsNone(pop._player.hyperparameters)
        self.assertIsNone(pop._player.interaction)
        self.assertEqual(pop._player.timestep, 2)
        self.assertNotEqual(pop._player.name, '')
        self.assert_invariants(pop)

    def test_with_pre_commit_hooks(self):
        pass
        # TODO

    def test_with_post_commit_hooks(self):
        pass
        # TODO
