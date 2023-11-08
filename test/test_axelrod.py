import axelrod as axl   # type: ignore

import unittest
from popcore import Population
# from popcore.utils import draw


class TestAxelrod(unittest.TestCase):

    def test_axelrod(self):
        """Example of usage of Population with axelrod"""

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

        branches = [pop.branch(str(p)) for p in players]

        for p, b in zip(players, branches):
            pop.checkout(b)
            pop.commit(p)

        for x in range(7):
            tournament = axl.Tournament(players)
            results = tournament.play()

            first = results.ranking[0]
            last = results.ranking[-1]

            pop.checkout(branches[first])
            branches[last] = pop.branch(str(players[first]) + str(x))

            players[last] = players[first]

            for p, b in zip(players, branches):
                pop.checkout(b)
                pop.commit(p)

        # draw(pop)
