# Create populations in different ways and for different situations to perform
# tests on them

from popcore.population import Population
import random

# TODO: @Szacquer document this example.


def mutate(parent_parameters, hyperparameters, contributors=[]):
    """Mutate a strand of DNA (replace a character in the str at random)"""
    next_dna = list(parent_parameters)
    next_dna[hyperparameters["spot"]] = hyperparameters["letter"]
    next_dna = ''.join(next_dna)
    return next_dna, hyperparameters


def random_linear_dna_evolution():
    """This tests the correctness of the case where the population consists
    of only a single lineage"""
    pop = Population()

    next_dna = "OOOOO"
    dna_history = [next_dna]

    pop.commit(parameters=next_dna)

    for x in range(16):
        letter = random.choice("ACGT")
        spot = random.randrange(len(next_dna))

        hyperparameters = {"letter": letter, "spot": spot}
        next_dna, _ = mutate(next_dna, hyperparameters)
        dna_history.append(next_dna)

        pop.commit(parameters=next_dna, hyperparameters=hyperparameters)

    return pop, dna_history


def nonlinear_population():
    """This tests the case where the population has multiple branches at
    different generations"""
    pop = Population()
    pop.branch("b1")
    pop.checkout("b1")
    pop.commit("1")
    pop.branch("b2")
    pop.checkout("b2")
    pop.commit("2")
    pop.commit("3")
    pop.checkout("_root")
    pop.branch("b3")
    pop.checkout("b3")
    pop.commit("4")
    pop.checkout("b1")
    pop.commit("5")
    pop.checkout('b2')

    return pop


def detach_from_pop():
    pop = Population()
    pop.branch("b1")
    pop.branch("b2")
    pop.checkout("b1")
    a = pop.commit(1)
    pop.commit(2)
    pop.checkout(a)
    pop.commit(3)
    pop.checkout("_root")
    pop.branch("b3")
    pop.checkout('b2')
    pop.commit(4)
    pop.commit(5)
    pop.commit(6)
    pop.branch("b4")
    pop.commit(7)
    pop.checkout("b4")
    pop.commit(8)
    pop.checkout("b3")
    a = pop.commit(9)
    b = pop.commit(15)
    pop.checkout(a)

    pop2 = pop.detach()
    pop2.branch("b1")
    pop2.checkout("b1")
    c = pop2.commit(10)
    pop2.commit(11)
    pop2.branch("b3")
    pop2.commit(12)
    pop2.checkout("b3")
    pop2.commit(13)
    pop2.checkout(pop2._root.id)
    d = pop2.commit(14)

    return pop, pop2, a, b, c, d
