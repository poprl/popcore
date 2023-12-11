import axelrod as axl   # type: ignore
from popcore.population import Population


def main():
    """Example: managing an evolving population with axelrod.

    We create a population of agents, and then
    1- Make the agents play a tournament
    2- Select the worst and best performing individuals
    3- Replace the worst agent with a copy of the best

    We repeat these steps for a few generations. This reproduces the original
    axelrod paper's concept.
    """

    # Create a population
    players = [
        axl.Cooperator(), axl.Defector(), axl.TitForTat(),
        axl.Grudger(), axl.Alternator(), axl.Aggravater(),
        axl.Adaptive(), axl.AlternatorHunter(), axl.ArrogantQLearner(),
        axl.Bully()
    ]

    with Population() as pop:
        # Each player has it's own branch (lineage) in the population
        branches = [
            pop.branch(str(p)) for p in players]

        # Commit the initial population of agents to their respective branches
        for player, branch in zip(players, branches):
            pop.checkout(branch)
            pop.commit(player)

        # Make a few generations of a tournament
        for i in range(7):
            # Play the tournament
            tournament = axl.Tournament(players)
            results = tournament.play()

            # Pick the best and worst players
            first = results.ranking[0]
            last = results.ranking[-1]

            # Replace the worst player with a copy of the best
            pop.checkout(branches[first])

            branches[last] = pop.branch(
                str(players[first]) + str(i)
            )
            players[last] = players[first]

            # Commit the members of the new generation to their respective
            # branches
            for player, branch in zip(players, branches):
                pop.checkout(branch)
                pop.commit(player)


if __name__ == "__main__":
    main()
