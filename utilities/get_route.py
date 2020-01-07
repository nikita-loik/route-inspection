import sys

import numpy as np

import matplotlib
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')

import networkx as nx
import shapely as sh

import utilities.globals as ug
import utilities.common as uc

import utilities.visualise_graph as vg

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(asctime)s: %(filename)s: %(lineno)s:\n%(message)s")
logger = logging.getLogger(__name__)


def get_virtual_path(
        g: nx.DiGraph,):
    virtual_circuit = list(nx.algorithms.euler.eulerian_circuit(g))
    return virtual_circuit


def get_real_path(
        virtual_circuit: list,
        g: nx.DiGraph,
        virtual_g: nx.DiGraph):
    real_circuit = []
    for e in virtual_circuit:
        if virtual_g.get_edge_data(*e)['type'] == 'segment':
            real_circuit.append(e)
        else:
            shortest_path = nx.shortest_path(g, *e)
            shortest_path_edges = [
                (shortest_path[i], shortest_path[i+1])
                for i in range(len(shortest_path) - 1)]
            real_circuit += shortest_path_edges
    
    circuit_by_node = [e[0] for e in real_circuit]
    logger.info(
        f"\teulerian circuit length {len(circuit_by_node)}\n")
    return {
        'circuit_by_edge': real_circuit,
        'circuit_by_node': circuit_by_node}


def get_random_path(
        g: nx.DiGraph,
):
    np.random.seed(0)
    visited_nodes = []
    next_node = np.random.choice(g.nodes())
    while len(set(visited_nodes)) < len(g.nodes):
        visited_nodes.append(next_node)
        possible_steps = [e[1] for e in g.out_edges(next_node)]
        next_node = np.random.choice(possible_steps)
    logger.info(
        f"\tUSING RANDOM WALK\n"
        f"\tvisited all nodes in {len(visited_nodes)}"
    )
    return visited_nodes

def get_random_path_with_min_repetitions(
        g: nx.DiGraph,
        ):
    np.random.seed(0)
    visited_nodes = []
    next_node = np.random.choice(g.nodes())
    while len(set(visited_nodes)) < len(g.nodes):
        visited_nodes.append(next_node)
        possible_steps = [e[1] for e in g.out_edges(next_node)]
        n_unseen_nodes = sum([1 for s in possible_steps if s not in visited_nodes])
        if n_unseen_nodes == 0 or n_unseen_nodes == len(possible_steps):
            step_probabilities = [1 / len(possible_steps) for s in possible_steps]
        else:
            step_probabilities = [(1 / n_unseen_nodes) if s not in visited_nodes else 0 for s in possible_steps]
        next_node = np.random.choice(possible_steps, p=step_probabilities)

    logger.info(
        f"\tUSING RANDOM WALK\n"
        f"\tvisited all nodes in {len(visited_nodes)}"
    )
    return visited_nodes