import unittest
from popcore._core import Interaction
from popcore.population import Population


class TestPopulation(unittest.TestCase):

    def test_init_with_default_args(self):
        with Population() as pop:
            self.assertEqual(pop.head(), pop._root)
            self.assertEqual(pop.head().id, "_root")

    def test_init_with_root_name(self):
        with Population(root_name="root beer") as pop:
            self.assertEqual(pop.head(), pop._root)
            self.assertEqual(pop.head().id, "root beer")

    def test_init_with_nondefault_stagedir(self):
        with Population(stage=".poptemp") as pop:
            self.assertEqual(pop.head(), pop._root)
            self.assertEqual(pop.head().id, "_root")
            self.assertEqual(pop.stage, ".poptemp")

    def test_branch_noargs_should_return_current(self):
        with Population() as pop:
            branch = pop.branch()

            self.assertEqual(branch, "main")
            self.assertEqual(pop.branches(), set(["main"]))

    def test_branch_with_name_should_create_branch(self):
        with Population() as pop:
            branch = pop.branch("branch1")
            self.assertEqual(branch, "branch1")
            self.assertEqual(pop.branches(), set(["main", "branch1"]))

    def test_branch_should_raise_if_branch_exists(self):
        with Population() as pop:
            pop.branch("branch1")
            self.assertRaises(ValueError, pop.branch, "branch1")

    def test_branch_should_raise_if_name_protected_main(self):
        with Population() as pop:
            self.assertRaises(ValueError, pop.branch, "main")

    def test_branch_should_raise_if_name_on_index(self):
        with Population() as pop:
            self.assertRaises(ValueError, pop.branch, "_root")

    def test_checkout_branch_should_return_checkout_branch(self):
        with Population() as pop:
            pop.branch("b1")
            pop.checkout("main")

            self.assertEqual(pop.branch(), "main")

    def test_checkout_should_change_branch_if_branch(self):
        with Population() as pop:
            pop.branch("b1")
            pop.checkout("b1")

            self.assertEqual(pop.branch(), "b1")

    def test_checkout_should_raise_if_branch_not_exist(self):
        with Population() as pop:
            pop.branch("b1")

            self.assertRaises(ValueError, pop.checkout, "b2")

    def test_should_commit_without_arguments(self):
        with Population() as pop:
            pop.commit()
            self.assertIsNone(pop.head().interaction)
            self.assertEqual(pop.head().timestep, 1)
            self.assertNotEqual(pop.head().id, None)

    def test_should_store_interaction(self):
        interaction = Interaction(["p1", "p2"], [1, 0])

        with Population() as pop:
            pop.commit(interaction=interaction)
            self.assertEqual(pop.head().interaction, interaction)
            self.assertEqual(pop.head().timestep, 1)
            self.assertNotEqual(pop.head().id, None)

    def test_should_commit_with_provided_id(self):
        with Population() as pop:
            pop.commit(id="Helloo")

            self.assertIsNone(pop.head().interaction)
            self.assertEqual(pop.head().timestep, 1)
            self.assertEqual(pop.head().id, 'Helloo')

    def test_should_raise_when_repeated_id(self):
        with Population() as pop:
            pop.commit(id="Helloo")
            self.assertRaises(ValueError, pop.commit, id="Helloo")

    def test_should_raise_with_internal_id(self):
        with Population() as pop:
            self.assertRaises(ValueError, pop.commit, id="_root")

    def test_should_raise_with_existing_branch(self):
        with Population() as pop:
            self.assertRaises(ValueError, pop.commit, id="main")

    def test_should_store_timestep(self):
        with Population() as pop:
            pop.commit(timestep=2)

            self.assertIsNone(pop.head().interaction)
            self.assertEqual(pop.head().timestep, 2)
            self.assertNotEqual(pop.head().id, '')
