import sys

import numpy as np
import shapely as sh
import networkx as nx
import matplotlib.pyplot as plt
import random

import utilities.globals as ug
import utilities.common as uc

import utilities.get_random_city as grc

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(asctime)s: %(filename)s: %(lineno)s:\n%(message)s")
logger = logging.getLogger(__name__)


# A. get simple graph =========================================================
def get_simple_graph(
        edges: list):
    g = nx.DiGraph()
    
    nodes = grc.get_nodes_dictionary(edges)
    for e in edges:
        tail = nodes[e['coordinates'][0]]
        head = nodes[e['coordinates'][1]]
        g.add_edge(
            tail,
            head,
            weight=0,
            edge_id=e['edge_id'],
            geometry=e['geometry'],
            coordinates=e['coordinates']
            )
        g.node[head]['coordinates'] = e['coordinates'][1]
        g.node[tail]['coordinates'] = e['coordinates'][0]

    connected_nodes = sorted(
        nx.strongly_connected_components(g),
        key=len,
        reverse=True)[0]
    disconnected_nodes = [
        n for n in list(g.nodes())
        if n not in connected_nodes]
    # g.remove_nodes_from(disconnected_nodes)

    return g

# B. get manoeuvre graph ======================================================
# def get_manoeuvre(
#         edge_i: dict,
#         edge_j: dict):
#     angle = uc.get_angle_between_two_edges(
#         edge_i, edge_j)

    # v_i = np.array([head - tail
    #     for tail, head in zip(*edge_i['coordinates'])])
    # v_j = np.array([head - tail
    #     for tail, head in zip(*edge_j['coordinates'])])
    # cosine = np.vdot(v_i, v_j) / (np.linalg.norm(v_i) * np.linalg.norm(v_j))
    # determinant = np.linalg.det([v_i, v_j])
    # if determinant < 0:
    #     angle = 180 * np.arccos(cosine) / np.pi
    # else:
    #     angle = 360 - (180 * np.arccos(cosine) / np.pi)
    
    # if 30 < angle <= 175:
    #     return 'turn_right'
    # elif 175 < angle <= 185:
    #     return 'make_u_turn'
    # elif 185 < angle <= 330:
    #     return 'turn_left'
    # elif (330 < angle) or (angle <= 30):
    #     return 'go_straight'


def get_manoeuvre_edge(
        edge_i: dict,
        edge_j: dict):
    if edge_i['coordinates'][1] == edge_j['coordinates'][0]:
        manoeuvre = uc.get_manoeuvre(edge_i, edge_j)
        coordinates = edge_i['coordinates'][1]
        return {'head': str(edge_j['edge_id']) + '_t',
                'tail': str(edge_i['edge_id']) + '_h',
                'coordinates': coordinates,
                'weight': ug.MANOEUVRE_PENALTY[manoeuvre],
                'geometry': sh.geometry.Point(coordinates),
                'manoeuvre': manoeuvre}
    else:
        return None


def get_manoeuvre_graph(
        edges: list):
    g = nx.DiGraph()

    # nodes = {}
    # sorted_nodes = sorted(
    #     list(set([p for s in edges for p in s['coordinates']])))
    # for p in sorted_nodes:
    #     nodes[p] = sorted_nodes.index(p)
    
    for edge in edges:
        tail = str(edge['edge_id']) + '_t'
        head = str(edge['edge_id']) + '_h'
        # tail = nodes[edge['coordinates'][0]]
        # head = nodes[edge['coordinates'][1]]
        
        g.add_edge(
            tail,
            head,
            weight=0,
            edge_id=edge['edge_id'],
            geometry=edge['geometry'],
            coordinates=edge['coordinates'],
            manoeuvre='go_straight'
            )
        g.node[head]['coordinates'] = edge['coordinates'][1]
        g.node[tail]['coordinates'] = edge['coordinates'][0]
    
    for edge_i in edges:
        for edge_j in edges:
            edge_data = get_manoeuvre_edge(edge_i, edge_j)
            if edge_data is not None:
                g.add_edge(
                    edge_data['tail'],
                    edge_data['head'],
                    weight=edge_data['weight'],
                    geometry=edge_data['geometry'],
                    coordinates=edge_data['coordinates'],
                    manoeuvre=edge_data['manoeuvre'])

    connected_nodes = sorted(
        nx.strongly_connected_components(g),
        key=len,
        reverse=True)[0]
    disconnected_nodes = [
        n for n in list(g.nodes())
        if n not in connected_nodes]
    g.remove_nodes_from(disconnected_nodes)
    return g


# C. get random district graph ================================================
def get_random_district_borders(
    city_size: list = ug.CITY_SIZE,
    district_size: list = ug.DISTRICT_SIZE):

    # western border - x_min
    x_min = random.randint(0, city_size[0]-district_size[0])
    # eastern border - x_max
    x_max = x_min + district_size[0]
    # southern border - y_min
    y_min = random.randint(0, city_size[1]-district_size[1])
    # nothern border - y_max
    y_max = y_min + district_size[1]
    district_borders = [(x_min, y_min),
        (x_max, y_max)]
    return district_borders


def check_node_within_district(
    district_borders: list,
    node_coordinates: list):
    node_coordinates
    if ((node_coordinates[0] < district_borders[0][0])
        or (node_coordinates[0] > district_borders[1][0])
        or (node_coordinates[1] < district_borders[0][1])
        or (node_coordinates[1] > district_borders[1][1])):
        return False
    else:
        return True
        

def get_random_district_graph(
        city_g: nx.DiGraph,
        city_size: list = ug.CITY_SIZE,
        district_size: list = ug.DISTRICT_SIZE,
        ) -> list:

    district_borders = get_random_district_borders(city_size, district_size)
    nodes_coordinates = nx.get_node_attributes(city_g, 'coordinates')
    district_g = city_g.copy()

    city_nodes = list(district_g.nodes())
    for n in city_nodes:
        node_coordinates = nodes_coordinates[n]
        if check_node_within_district(
            district_borders,
            node_coordinates) is False:
            district_g.remove_node(n)

    logging.info(
        f"district borders:\n"
        f"west-east: {district_borders[0][0]} - {district_borders[1][0]}\n"
        f"south-north: {district_borders[0][1]} - {district_borders[1][1]}")
    return district_g


# D. get inverted graph =======================================================
def get_inverted_edge(
        edge_i: dict,
        edge_j: dict):
    if edge_i['coordinates'][1] == edge_j['coordinates'][0]:
        manoeuvre = uc.get_manoeuvre(edge_i, edge_j)
        coordinates = [tuple([tail + (head - tail) / 2
            for tail, head in zip(*edge_i['coordinates'])]),
            tuple([tail + (head - tail) / 2
            for tail, head in zip(*edge_j['coordinates'])])]

        return {'head': edge_j['edge_id'],
                'tail': edge_i['edge_id'],
                'coordinates': coordinates,
                'weight': ug.MANOEUVRE_PENALTY[manoeuvre],
                'geometry': sh.geometry.LineString(coordinates),
                'manoeuvre': manoeuvre}
    else:
        return None


def get_inverted_graph(
        edges: list):
    g = nx.DiGraph()
    
    for edge_i in edges:
        for edge_j in edges:
            edge_data = get_inverted_edge(edge_i, edge_j)
            if edge_data is not None:
                g.add_edge(
                    edge_data['tail'],
                    edge_data['head'],
                    weight=edge_data['weight'],
                    geometry=edge_data['geometry'],
                    coordinates=edge_data['coordinates'],
                    manoeuvre=edge_data['manoeuvre'])

                g.node[
                    edge_data['head']][
                        'coordinates'] = edge_data['coordinates'][1]
                g.node[
                    edge_data['tail']][
                        'coordinates'] = edge_data['coordinates'][0]
    
    connected_nodes = sorted(
        nx.strongly_connected_components(g),
        key=len,
        reverse=True)[0]
    disconnected_nodes = [
        n for n in list(g.nodes())
        if n not in connected_nodes]
    g.remove_nodes_from(disconnected_nodes)
    return g