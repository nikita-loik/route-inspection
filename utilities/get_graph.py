import sys

import numpy as np
import shapely as sh
import networkx as nx
import matplotlib.pyplot as plt
import random

import utilities.globals as g_globals

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(asctime)s: %(filename)s: %(lineno)s:\n%(message)s")
logger = logging.getLogger(__name__)


# A. get city graph ===========================================================
def get_crossroads_dictionary(
        segments: list):
    segments_coordinates = [segment['coordinates']
        for segment in segments]
    sorted_coordinates = sorted(list(set([c
        for coordinates in segments_coordinates
        for c in coordinates])))
    crossroads = {c: sorted_coordinates.index(c)
        for c in sorted_coordinates}
    return crossroads


def get_city_graph(
        segments: list):
    g = nx.DiGraph()
    
    crossroads = get_crossroads_dictionary(segments)
    for segment in segments:
        head = crossroads[segment['coordinates'][1]]
        tail = crossroads[segment['coordinates'][0]]
        g.add_edge(
            tail,
            head,
            weight=0,
            segment_id=segment['segment_id'],
            geometry=segment['geometry'],
            coordinates=segment['coordinates']
            )
        g.node[head]['coordinates'] = segment['coordinates'][1]
        g.node[tail]['coordinates'] = segment['coordinates'][0]

    # connected_nodes = sorted(
    #     nx.strongly_connected_components(g),
    #     key=len,
    #     reverse=True)[0]
    # disconnected_nodes = [
    #     n for n in list(g.nodes())
    #     if n not in connected_nodes]
    # g.remove_nodes_from(disconnected_nodes)
    return g

# B. get manoeuvre graph ======================================================
def get_manoeuvre(
        i_segment: dict,
        j_segment: dict):
    
    v_i = np.array([head - tail
        for tail, head in zip(*i_segment['coordinates'])])
    v_j = np.array([head - tail
        for tail, head in zip(*j_segment['coordinates'])])
    cosine = np.vdot(v_i, v_j) / (np.linalg.norm(v_i) * np.linalg.norm(v_j))
    determinant = np.linalg.det([v_i, v_j])
    if determinant < 0:
        angle = 180 * np.arccos(cosine) / np.pi
    else:
        angle = 360 - (180 * np.arccos(cosine) / np.pi)
    
    if 30 < angle <= 175:
        return 'turn_right'
    elif 175 < angle <= 185:
        return 'make_u_turn'
    elif 185 < angle <= 330:
        return 'turn_left'
    elif (330 < angle) or (angle <= 30):
        return 'go_straight'


def get_manoeuvre_edge(
        i_segment: dict,
        j_segment: dict):
    if i_segment['coordinates'][1] == j_segment['coordinates'][0]:
        manoeuvre = get_manoeuvre(i_segment, j_segment)
        coordinates = i_segment['coordinates'][1]
        return {'head': str(j_segment['segment_id']) + '_t',
                'tail': str(i_segment['segment_id']) + '_h',
                'coordinates': coordinates,
                'weight': g_globals.MANOEUVRE_PENALTY[manoeuvre],
                'geometry': sh.geometry.Point(coordinates),
                'manoeuvre': manoeuvre}
    else:
        return None


def get_manoeuvre_graph(
        segments: list):
    g = nx.DiGraph()
    
    for segment in segments:
        head = str(segment['segment_id']) + '_h'
        tail = str(segment['segment_id']) + '_t'
        g.add_edge(
            tail,
            head,
            weight=0,
            segment_id=segment['segment_id'],
            geometry=segment['geometry'],
            coordinates=segment['coordinates'],
            manoeuvre='go_straight'
            )
        g.node[head]['coordinates'] = segment['coordinates'][1]
        g.node[tail]['coordinates'] = segment['coordinates'][0]
    
    for i_segment in segments:
        for j_segment in segments:
            edge_data = get_manoeuvre_edge(i_segment, j_segment)
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
    city_size: list = g_globals.CITY_SIZE,
    district_size: list = g_globals.DISTRICT_SIZE):
    
    western_border = random.randint(0, city_size[0]-district_size[0])
    eastern_border = western_border + district_size[0]
    southern_border = random.randint(0, city_size[1]-district_size[1])
    nothern_border = southern_border + district_size[1]
    district_borders = [(western_border, southern_border),
        (eastern_border, nothern_border)]
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
        city_size: list = g_globals.CITY_SIZE,
        district_size: list = g_globals.DISTRICT_SIZE,
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
        i_segment: dict,
        j_segment: dict):
    if i_segment['coordinates'][1] == j_segment['coordinates'][0]:
        manoeuvre = get_manoeuvre(i_segment, j_segment)
        coordinates = [tuple([tail + (head - tail) / 2
            for tail, head in zip(*i_segment['coordinates'])]),
            tuple([tail + (head - tail) / 2
            for tail, head in zip(*j_segment['coordinates'])])]

        return {'head': j_segment['segment_id'],
                'tail': i_segment['segment_id'],
                'coordinates': coordinates,
                'weight': g_globals.MANOEUVRE_PENALTY[manoeuvre],
                'geometry': sh.geometry.LineString(coordinates),
                'manoeuvre': manoeuvre}
    else:
        return None


def get_inverted_graph(
        segments: list):
    g = nx.DiGraph()
    
    for i_segment in segments:
        for j_segment in segments:
            edge_data = get_inverted_edge(i_segment, j_segment)
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