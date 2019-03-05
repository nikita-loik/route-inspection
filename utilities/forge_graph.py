import sys

import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import shapely as sh

import utilities.globals as g_globals
import utilities.visualise_graph as vg

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(asctime)s: %(filename)s: %(lineno)s:\n%(message)s")
logger = logging.getLogger(__name__)


# get graph condensations =====================================================
def condence_nodes(
    g: nx.DiGraph,
    nodes_to_condence: list,
    new_node: str,
    coordinates: tuple):
#     https://gist.github.com/Zulko/7629206
    
    g.add_node(new_node, coordinates=coordinates) # add condensation node
    
    g_edges = list(g.edges(data=True))
    for tail_n, head_n, data in g_edges:
        # For all edges related to one of the nodes to condence,
        # make an edge going to or coming from the `new gene`.
        if tail_n in nodes_to_condence:
            g.add_edge(new_node, head_n, manoeuvre='quasi_manoeuvre')
        elif head_n in nodes_to_condence:
            g.add_edge(tail_n, new_node, manoeuvre='quasi_manoeuvre')
    
    for n in nodes_to_condence: # Remove the condenced nodes
        g.remove_node(n)


# add grafts to graph =========================================================
def get_grafting_nodes_and_edges(
    g: nx.DiGraph,
    super_g: nx.DiGraph,
    condenced_g: nx.DiGraph,
    source_node: str = None,
    target_node: str = None):
    
    nodes_to_add = nx.shortest_path(
        condenced_g,
        source_node,
        target_node)[1:-1]
    edges_to_add = [(nodes_to_add[i], nodes_to_add[i+1])
        for i in range(len(nodes_to_add)-1)]

    for tail, head in super_g.in_edges(nodes_to_add[0]):
        if tail in g.nodes:
            edges_to_add.append((tail,head))
            nodes_to_add.append(head)
        # else:
        #     logger.info("01 wrong tail")

    for tail, head in super_g.in_edges(nodes_to_add[-1]):
        if head in g.nodes:
            edges_to_add.append((tail,head))
            nodes_to_add.append(tail)
        # else:
        #     logger.info("02 wrong head")

    logger.info(
        f"nodes to add: {nodes_to_add}\n"
        f"edges to add: {edges_to_add}"
        )

    return {'nodes_to_add': nodes_to_add,
            'edges_to_add': edges_to_add}


def add_connecting_grafts(
    g: nx.DiGraph,
    super_g: nx.DiGraph):

    g_scc = sorted(
        list(nx.strongly_connected_components(g)),
        key=len,
        reverse=True)
    condenced_g = super_g.copy()
    
    # select two biggest strongly connected components (scc)
    for i, scc in enumerate(g_scc[:2]):
        scc_coordinates = list(
            zip(*[super_g.nodes(data=True)[n]['coordinates']
            for n in scc]))
        condensation_coordinates = tuple(
            [np.mean(c)
            for c in scc_coordinates])
        condence_nodes(
            condenced_g,
            scc,
            # 'condensation_node',
            i,
            condensation_coordinates)
    # vg.visualise_manoeuvre_graph(condenced_g)
    nodes_to_add = []
    edges_to_add = []
    for n in get_grafting_nodes_and_edges(
        g, super_g, condenced_g, 0, 1)['nodes_to_add']:
        nodes_to_add.append(n)
    for e in get_grafting_nodes_and_edges(
        g, super_g, condenced_g, 0, 1)['edges_to_add']:
        edges_to_add.append(e)
    for n in get_grafting_nodes_and_edges(
        g, super_g, condenced_g, 1, 0)['nodes_to_add']:
        nodes_to_add.append(n)
    for e in get_grafting_nodes_and_edges(
        g, super_g, condenced_g, 1, 0)['edges_to_add']:
        edges_to_add.append(e)

    logger.info(
        f"added edges: {edges_to_add}\n"
        f"added nodes: {nodes_to_add}")

    working_g = g.copy()
    for tail, head in edges_to_add:
        edge_data=super_g.get_edge_data(tail, head)
        working_g.add_edge(
                tail,
                head,
                weight=edge_data['weight'],
                geometry=edge_data['geometry'],
                coordinates=edge_data['coordinates'],
                manoeuvre=edge_data['manoeuvre'])
    nodes_coordinates = nx.get_node_attributes(super_g, 'coordinates')
    for n in nodes_to_add:
        working_g.node[n]['coordinates'] = nodes_coordinates[n]

    # ugly way to remove disconnected nodes;
    # in fact, they should not be included into the graph from the very start.
    connected_nodes = sorted(
        nx.strongly_connected_components(working_g),
        key=len,
        reverse=True)[0]
    disconnected_nodes = []
    for n in working_g.nodes():
        if n not in connected_nodes:
            disconnected_nodes.append(n)
    working_g.remove_nodes_from(disconnected_nodes)

    return working_g

