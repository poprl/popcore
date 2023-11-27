import axelrod as axl   # type: ignore
from popcore.population import Population


def main():
    """Example of usage of Population with axelrod"""
    # TODO: @Scezaquer document this example (i.e., what the purpose?)
    players = [
        axl.Cooperator(), axl.Defector(), axl.TitForTat(),
        axl.Grudger(), axl.Alternator(), axl.Aggravater(),
        axl.Adaptive(), axl.AlternatorHunter(), axl.ArrogantQLearner(),
        axl.Bully()
    ]

    with Population() as pop:
        branches = [
            pop.branch(str(p)) for p in players]

        for player, branch in zip(players, branches):
            pop.checkout(branch)
            pop.commit(player)

        for i in range(7):
            tournament = axl.Tournament(players)
            results = tournament.play()

            first = results.ranking[0]
            last = results.ranking[-1]

            pop.checkout(branches[first])

            branches[last] = pop.branch(
                str(players[first]) + str(i)
            )
            players[last] = players[first]

            for player, branch in zip(players, branches):
                pop.checkout(branch)
                pop.commit(player)


if __name__ == "__main__":
    main()
