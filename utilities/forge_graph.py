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

    # logger.info(
    #     f"nodes to add: {nodes_to_add}\n"
    #     f"edges to add: {edges_to_add}"
    #     )

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
                manoeuvre=edge_data['manoeuvre'])
    nodes_coordinates = nx.get_node_attributes(super_g, 'coordinates')
    for n in nodes_to_add:
        working_g.node[n]['coordinates'] = nodes_coordinates[n]

    # ugly way to remove disconnected nodes;
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


# join edges in graph =========================================================
def join_two_linestrings(
        linestring_i,
        linestring_j,
        ):
    '''
    Takes two linestrings.
    NB! asumes linestring_i has correct geometry,
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


def get_splitting_nodes(
        g: nx.DiGraph
        ):
    splitting_nodes = []
    # for n in g.nodes():
    #     if ((len(g.in_edges(n))==1)
    #         and (len(g.out_edges(n))==1)):
    #         edge_i = g.get_edge_data(*list(g.in_edges(n))[0])
    #         edge_j = g.get_edge_data(*list(g.out_edges(n))[0])
    #         if uc.get_manoeuvre(
    #             edge_i, edge_j) == 'go_straight':
    #             splitting_nodes.append(n)
    for n in g.nodes():
        if ((len(g.in_edges(n))==1)
            and (len(g.out_edges(n))==1)):
            segment_i = g.get_edge_data(*list(g.in_edges(n))[0])
            segment_j = g.get_edge_data(*list(g.out_edges(n))[0])
            if ((segment_i['manoeuvre'] == 'go_straight')
                and (segment_j['manoeuvre'] == 'go_straight')):
                splitting_nodes.append(n)
    return splitting_nodes

def join_split_edges(
        g: nx.DiGraph
        ):
    splitting_nodes = get_splitting_nodes(g)
    while len(splitting_nodes) > 0:
        g = join_edges(g, splitting_nodes)
    logger.info(f"removed {len(splitting_nodes)} nodes")
    return g


# def get_combined_geometry_and_direction(e_a_data, e_b_data):
#     if (e_a_data['direction'] == 3 and e_b_data['direction'] != 3):
#         combined_geometry = join_two_linestrings(
#             e_b_data['geometry'],
#             e_a_data['geometry'])
#         return {'geometry': combined_geometry,
#                 'direction': e_b_data['direction']}
#     else:
#         combined_geometry = join_two_linestrings(
#             e_a_data['geometry'],
#             e_b_data['geometry'])
#         return {'geometry': combined_geometry,
#                 'direction': e_a_data['direction']}


def join_edges(
        g: nx.DiGraph,
        splitting_nodes: list,
        ):
    print(splitting_nodes)
    for n in splitting_nodes:
        edge_i = g.get_edge_data(*list(g.in_edges(n))[0])
        edge_j = g.get_edge_data(*list(g.out_edges(n))[0])
        combined_geometry = join_two_linestrings(
            edge_i['geometry'],
            edge_j['geometry'])
        combined_coordinates = [
            edge_i['coordinates'][0],
            edge_j['coordinates'][1]]
        tail = list(g.in_edges(n))[0][0]
        head = list(g.in_edges(n))[0][1]
        # tail = list(g.neighbors(n))[0]
        # head = list(g.neighbors(n))[1]
        working_g = g.copy()
        working_g.add_edge(
            tail,
            head,
            weight=combined_geometry.length,
            edge_id=str(edge_i['edge_id']),
            geometry=combined_geometry,
            coordinates=combined_coordinates
            )
        working_g.remove_node(n) 
        return working_g
    else:
        return g