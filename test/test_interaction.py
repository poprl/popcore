import unittest

from popcore import Interaction


class TestInteraction(unittest.TestCase):

    def test_conversion_to_pairwise_should_keep_order_2(self):
        interaction = Interaction(
            players=["a", "b"],
            outcomes=[1, 2]
        )

        self.assertEqual(
            [interaction],
            interaction.to_pairwise()
        )

    def test_conversion_to_pairwise_should_split(self):
        interaction = Interaction(
            players=["a", "b", "c"],
            outcomes=[1, 2, 3]
        )

        pairwise = [
            Interaction(["a", "b"], [1, 2]),
            Interaction(["a", "c"], [1, 3]),
            Interaction(["b", "c"], [2, 3])
        ]

        self.assertListEqual(
            pairwise,
            interaction.to_pairwise()
        )
