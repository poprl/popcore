# Create populations in different ways and for different situations to perform
# tests on them

from popcore.population import Population
import random


def mutate(parent_parameters, hyperparameters, contributors=[]):
    """Mutate a strand of DNA (replace a character in the str at random)"""
    new_DNA = list(parent_parameters)
    new_DNA[hyperparameters["spot"]] = hyperparameters["letter"]
    new_DNA = ''.join(new_DNA)
    return new_DNA, hyperparameters


def random_linear_dna_evolution():
    """This tests the correctness of the case where the population consists
    of only a single lineage"""
    pop = Population()

    new_DNA = "OOOOO"
    DNA_history = [new_DNA]

    pop.commit(parameters=new_DNA)

    for x in range(16):
        letter = random.choice("ACGT")
        spot = random.randrange(len(new_DNA))

        hyperparameters = {"letter": letter, "spot": spot}
        new_DNA, _ = mutate(new_DNA, hyperparameters)
        DNA_history.append(new_DNA)

        pop.commit(parameters=new_DNA, hyperparameters=hyperparameters)

    return pop, DNA_history


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
