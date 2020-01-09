import os, sys, inspect

import numpy as np

import matplotlib
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')

import networkx as nx
import shapely as sh

import utilities.global_parameters as ug
import utilities.common as uc

import utilities.visualise_graph as vg

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(asctime)s: %(filename)s: %(lineno)s:\n%(message)s")
logger = logging.getLogger(__name__)


# CONDENSE NODES ==============================================================
def condense_nodes(
        g: nx.DiGraph,
        nodes_to_condense: list,
        new_node_name: str,
        new_node_coordinates: tuple) -> nx.DiGraph:
    '''
    https://gist.github.com/Zulko/7629206
    Condense (merge) multiple nodes into one:
    for all edges going to or coming from one of the 'old nodes',
    make an edge going to or coming from the 'new node'.
    INPUT
    g                       graph (nx.DiGraph)
    nodes_to_condense       node names to condense (list)
    new_node_name           condensation-node name (str)
    new_node_coordinates    condensation-node coordinates (str)
    ------------
    OUTPUT
    g   graph (nx.DiGraph)
    '''
    
    g.add_node(
        new_node_name,
        coordinates=new_node_coordinates) # add condensation node
    
    g_edges = list(g.edges(data=True))
    for tail, head, data in g_edges:
        if tail in nodes_to_condense:
            g.add_edge(
                new_node_name,
                head,
                coordinates=[new_node_coordinates, data['coordinates'][1]],
                manoeuvre='quasi_manoeuvre',
                type='segment')
        elif head in nodes_to_condense:
            g.add_edge(
                tail,
                new_node_name,
                coordinates=[data['coordinates'][0], new_node_coordinates],
                manoeuvre='quasi_manoeuvre',
                type='segment')
    
    for n in nodes_to_condense: # remove the condensed nodes
        g.remove_node(n)
    return g


# add grafts to graph =========================================================
def get_grafting_nodes_and_edges(
    g: nx.DiGraph,
    super_g: nx.DiGraph,
    condensed_g: nx.DiGraph,
    source_node: str = None,
    target_node: str = None):
    
    nodes_to_add = nx.shortest_path(
        condensed_g,
        source_node,
        target_node)[1:-1]
    edges_to_add = [(nodes_to_add[i], nodes_to_add[i+1])
        for i in range(len(nodes_to_add)-1)]

    for tail, head in super_g.in_edges(nodes_to_add[0]):
        if tail in g.nodes:
            edges_to_add.append((tail, head))
            nodes_to_add.append(head)

    for tail, head in super_g.in_edges(nodes_to_add[-1]):
        if head in g.nodes:
            edges_to_add.append((tail, head))
            nodes_to_add.append(tail)

    return {'nodes_to_add': nodes_to_add,
            'edges_to_add': edges_to_add}


def add_connecting_grafts(
    g: nx.DiGraph,
    super_g: nx.DiGraph):

    # Get strongly connected components.
    g_scc = sorted(
        list(nx.strongly_connected_components(g)),
        key=len,
        reverse=True)
    condensed_g = super_g.copy()
    # Select two biggest strongly connected components (scc).
    for i, scc in enumerate(g_scc[:2]):
        scc_coordinates = list(
            zip(*[super_g.nodes(data=True)[n]['coordinates']
            for n in scc]))
        condensation_coordinates = tuple(
            [np.mean(c)
            for c in scc_coordinates])
        condensed_g = condense_nodes(
            condensed_g,
            scc,
            i,
            condensation_coordinates)
        # print(condensed_g.nodes())
    # vg.visualise_manoeuvre_graph(condensed_g)
    nodes_to_add = []
    edges_to_add = []
    grafting_n_e_0_to_1 = get_grafting_nodes_and_edges(
        g, super_g, condensed_g, 0, 1)
    for n in grafting_n_e_0_to_1['nodes_to_add']:
        nodes_to_add.append(n)
    for e in grafting_n_e_0_to_1['edges_to_add']:
        edges_to_add.append(e)
    grafting_n_e_1_to_0 = get_grafting_nodes_and_edges(
        g, super_g, condensed_g, 1, 0)
    for n in grafting_n_e_1_to_0['nodes_to_add']:
        nodes_to_add.append(n)
    for e in grafting_n_e_1_to_0['edges_to_add']:
        edges_to_add.append(e)

    # logger.info(
    #     f"added edges: {edges_to_add}\n"
    #     f"added nodes: {nodes_to_add}")

    working_g = g.copy()
    for tail, head in edges_to_add:
        edge_data=super_g.get_edge_data(tail, head)
        working_g.add_edge(
                tail,
                head,
                weight=edge_data['weight'],
                geometry=edge_data['geometry'],
                coordinates=edge_data['coordinates'],
                manoeuvre=edge_data['manoeuvre'],
                type=edge_data['type'])
    nodes_coordinates = nx.get_node_attributes(super_g, 'coordinates')
    for n in nodes_to_add:
        nx.set_node_attributes(
            working_g,
            {'coordinates': nodes_coordinates[n]})

    # an ugly way to remove disconnected nodes;
    # in fact, they should not be included into the graph from the very start.
    # connected_nodes = sorted(
    #     nx.strongly_connected_components(working_g),
    #     key=len,
    #     reverse=True)[0]
    # disconnected_nodes = []
    # for n in working_g.nodes():
    #     if n not in connected_nodes:
    #         disconnected_nodes.append(n)
    # working_g.remove_nodes_from(disconnected_nodes)

    return working_g


def remove_single_nodes(
        g: nx.DiGraph
        ):
    working_g = g.copy()
    g_scc = sorted(
        list(nx.strongly_connected_components(g)),
        key=len,
        reverse=True)
    for c in g_scc:
        if len(c) == 1:
            working_g.remove_nodes_from(c)
    return working_g


# join edges in graph =========================================================
def join_two_linestrings(
        linestring_i,
        linestring_j,
        ):
    '''
    Takes two linestrings.
    NB! assumes linestring_i has correct geometry,
    therefore linestring_i geometry is never inverted
    '''
    coords_i = list(linestring_i.coords)
    coords_j = list(linestring_j.coords)
    if coords_i[0] == coords_j[0]:
        new_coords = coords_j[::-1][:-1] + coords_i
        return sh.geometry.LineString(new_coords)
    elif coords_i[0] == coords_j[-1]:
        new_coords = coords_j[:-1] + coords_i
        return sh.geometry.LineString(new_coords)
    elif coords_i[-1] == coords_j[0]:
        new_coords = coords_i + coords_j[1:]
        return sh.geometry.LineString(new_coords)
    elif coords_i[-1] == coords_j[-1]:
        new_coords = coords_i + coords_j[::-1][1:]
        return sh.geometry.LineString(new_coords)


def is_joinable(
        g: nx.DiGraph,
        n: str) -> bool:

    adjacent_edge_tail = [
        e for e in g.out_edges(n)
        if g.get_edge_data(*e)['manoeuvre'] == 'go_straight'][0][1]
    in_edges = g.in_edges(adjacent_edge_tail)
    ways_in = [
        g.get_edge_data(*e)['manoeuvre']
        for e in in_edges]
    # Check whether 'turn_right' or 'turn_left' are possible ways_in.
    if 'turn_right' in ways_in or 'turn_left' in ways_in:
        return False
    else:
        return True


def get_splitting_nodes(
        g: nx.DiGraph
        ):
    '''
    INPUT
    NetworkX directed graph (nx.classes.digraph.DiGraph).
    ------------
    OUTPUT
    list of splitting nodes (i.e. nodes, in-comming and out-going edges which
    can be reconnected, thus simplifying the graph)
    '''
    splitting_nodes = []
    for n in g.nodes():
        if g.out_degree[n] == 1:
            out_edge = list(g.out_edges(n))[0]
            escape = g.get_edge_data(*out_edge)['manoeuvre']
            escape_coordinates = g.get_edge_data(*out_edge)['coordinates']
            # Check whether it is a manoeuvre edge and whether it reads 'go_straight'.
            if (
                len(escape_coordinates) == 1 and
                escape == 'go_straight' and
                is_joinable(g, n)):
                splitting_nodes.append(n)
        if g.out_degree[n] == 2:
            out_edges = g.out_edges(n)
            ways_out = [
                g.get_edge_data(*e)['manoeuvre']
                for e in out_edges]
            # Check whether 'go_straight' and 'make_u_turn' are the only two ways_out.
            if (
                'go_straight' in ways_out and
                'make_u_turn' in ways_out and
                is_joinable(g, n)):
                splitting_nodes.append(n)
    return splitting_nodes

def join_split_edges(
        g: nx.DiGraph
        ):
    splitting_nodes = get_splitting_nodes(g)
    n_nodes_to_remove = len(splitting_nodes)
    while len(splitting_nodes) > 0:
        g = join_edges(g, splitting_nodes)
        splitting_nodes = get_splitting_nodes(g)
    logger.info(f"\tremoved {n_nodes_to_remove} nodes")
    return g


def join_edges(
        g: nx.DiGraph,
        splitting_nodes: list,
        ):
    working_g = g.copy()
    for n in splitting_nodes:
        edge_in = list(working_g.in_edges(n))[0]
        edge_in_data = working_g.get_edge_data(*edge_in)
        go_straight_manoeuvre = [
            e for e in working_g.out_edges(n)
            if working_g.get_edge_data(*e)['manoeuvre'] == 'go_straight'][0]
        edge_out = [
            e for e in working_g.out_edges(go_straight_manoeuvre[1])
            if working_g.get_edge_data(*e)['manoeuvre'] == 'go_straight'][0]
        edge_out_data = working_g.get_edge_data(*edge_out)
        combined_geometry = join_two_linestrings(
            edge_in_data['geometry'],
            edge_out_data['geometry'])
        combined_coordinates = [
            edge_in_data['coordinates'][0],
            edge_out_data['coordinates'][1]]
        tail = edge_in[0]
        head = edge_out[1]
        working_g.add_edge(
            tail,
            head, 
            weight=combined_geometry.length,
            edge_id=str(edge_in_data['edge_id']),
            geometry=combined_geometry,
            manoeuvre='go_straight',
            coordinates=combined_coordinates,
            type='segment',
            )
        working_g.remove_node(edge_in[1])
        working_g.remove_node(edge_out[0])
    return working_g

# PRUNE GRAPH =================================================================
def sort_edges_by_pairs(
        edges: list,
        ) -> list:
    edges_sorted = []
    for e in edges:
        if e not in edges_sorted:
            edges_sorted.append(e)
            if (((e[0] * e[1]) < 0) and
                ((-e[0], -e[1]) in edges) and
                ((-e[0], -e[1]) not in edges_sorted)):
                edges_sorted.append((-e[0], -e[1]))
    return edges_sorted


def prune_u_turns(
        g: nx.DiGraph):
    edges = list(g.edges())
    # NB! For small graphs, produces much neater result,
    # with fewer edges to be added when balancing the nodes.
    # For big graphs doesn't make any difference.
    edges_sorted = sort_edges_by_pairs(edges)
    # edges_sorted = edges
    for e in edges_sorted:
        manoeuvre = g.get_edge_data(*e)['manoeuvre']
        if manoeuvre == 'make_u_turn':
            test_g = g.copy()
            test_g.remove_edge(*e)
            if nx.is_strongly_connected(test_g):
                g.remove_edge(*e)
    return g
                
def prune_left_turns(
        g: nx.DiGraph):
    edges = list(g.edges())
    for e in edges:
        manoeuvre = g.get_edge_data(*e)['manoeuvre']
        if manoeuvre == 'turn_left':
            test_g = g.copy()
            test_g.remove_edge(*e)
            if nx.is_strongly_connected(test_g):
                g.remove_edge(*e)
    return g


def prune_right_turns(
        g: nx.DiGraph):
    edges = list(g.edges())
    for e in edges:
        manoeuvre = g.get_edge_data(*e)['manoeuvre']
        if manoeuvre == 'right_left':
            test_g = g.copy()
            test_g.remove_edge(*e)
            if nx.is_strongly_connected(test_g):
                g.remove_edge(*e)
    return g

# BALLANCE NODES ==============================================================
def get_imbalanced_nodes(
        g: nx.DiGraph):
    '''
    INPUT
    directed graph
    OUTPUT
    dict
    excess_ins      nodes with more in-coming than out-going edges (list)
    excess_outs     nodes with more out-going than in-coming edges (list)
    '''
    excess_ins = []
    excess_outs = []
    for n in g.nodes():
        in_degree = g.in_degree(n)
        out_degree = g.out_degree(n)
        if in_degree > out_degree:
            excess_ins.append(n)
        if in_degree < out_degree:
            excess_outs.append(n)
    logger.info(
        f"\tnodes # {len(g.nodes())}\n"
        f"\tedges # {len(g.edges())}\n"
        f"\tIMBALANCED NODES:\n"
        f"\texcess ins # {len(excess_ins)}\n"
        # f"\t{excess_ins}\n"
        f"\texcess outs # {len(excess_outs)}\n"
        # f"\t{excess_outs}\n"
    )
    return {
        'excess_ins': excess_ins,
        'excess_outs': excess_outs}


def get_virtual_edges(
        g: nx.DiGraph,
        ):
    imbalanced_nodes = get_imbalanced_nodes(g)
    excess_ins = imbalanced_nodes['excess_ins']
    excess_outs = imbalanced_nodes['excess_outs']
    virtual_edges = []
    for n in excess_ins:
        shortest_path = len(g.edges())
        nearest_node = None
        for m in excess_outs:
            path = nx.shortest_path_length(
                g,
                source=n,
                target=m)
            if (
                path < shortest_path and
                (n, m) not in g.edges()):
                shortest_path = path
                nearest_node = m
        if nearest_node is None:
            break
        else:
            virtual_edges.append((n, nearest_node))
            excess_outs.remove(nearest_node)
    logger.info(
        f"\tvirtual edges # {len(virtual_edges)}\n")
    return virtual_edges


def balance_graph_iteratively(
        g: nx.DiGraph):

    virtual_g = g.copy()
    n_cycles = 0
    n_edges_added = 0
    while nx.is_eulerian(virtual_g) is False:
        n_cycles += 1
        virtual_edges = get_virtual_edges(virtual_g)
        n_edges_added += len(virtual_edges)
        virtual_g.add_edges_from(
            virtual_edges,
            type='virtual_edge')
    logger.info(
        f"\tadded {n_edges_added} edges over {n_cycles} cycles\n")
    return virtual_g