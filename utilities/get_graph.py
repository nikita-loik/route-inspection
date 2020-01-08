import os, sys, inspect

import numpy as np
import shapely as sh
import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')
import random

import utilities.global_parameters as ug
import utilities.common as uc

import utilities.get_random_city as grc

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(asctime)s: %(filename)s: %(lineno)s:\n%(message)s")
logger = logging.getLogger(__name__)


# A. GET NAIVE GRAPH ==========================================================
def get_points_dictionary(
        segments: list
        ) -> dict:
    '''
    INPUT
    segments data (list of dicts)
        ...
        coordinates start and end point of a segment (list of tuples)
        ...
    ------------
    OUTPUT
    points ids (dict)
        point coordinates (tuple)   point id (int)
    '''
    points_coordinates = {}
    sorted_points_coordinates = sorted(
        list(set([n for s in segments for n in s['coordinates']])))
    for n in sorted_points_coordinates:
        points_coordinates[n] = sorted_points_coordinates.index(n)
    return points_coordinates


def get_naive_graph(
        edges: list):
    '''
    INPUT
    edges (list of dicts)
        segment_id  unique id (int)
        direction (int)
        coordinates start and end point of a segment (list of tuples)
        geometry    (shapely linestring)
    ------------
    OUTPUT
    g   graph (nx.DiGraph)
        nodes   point coordinates (tuple)
        edges
            u           start-node coordinates (tuple)
            v           end-node coordinates (tuple)
            weight      edge weight
            edge_id     segment id
            geometry    segment geometry (shapely linestring)
            coordinates start and end node of a edge (list of tuples)
    '''
    g = nx.DiGraph()
    
    for e in edges:
        tail = e['coordinates'][0]
        head = e['coordinates'][1]
        g.add_edge(
            tail,
            head,
            weight=0,
            edge_id=e['segment_id'],
            geometry=e['geometry'],
            coordinates=e['coordinates']
            )
        attributes = {
            head: {'coordinates': head}, 
            tail: {'coordinates': tail},
            }
        nx.set_node_attributes(g, attributes)

    connected_nodes = sorted(
        nx.strongly_connected_components(g),
        key=len,
        reverse=True)[0]
    disconnected_nodes = [
        n for n in list(g.nodes())
        if n not in connected_nodes]
    g.remove_nodes_from(disconnected_nodes)

    return g


# B. GET MANOEUVRE GRAPH ======================================================
def get_manoeuvre_data(
        edge_in: dict,
        edge_out: dict):
    '''
    INPUT
    ------------
    OUTPUT
    '''
    if edge_in['coordinates'][1] == edge_out['coordinates'][0]:
        manoeuvre = uc.get_manoeuvre(edge_in, edge_out)
        coordinates = [edge_in['coordinates'][1], edge_out['coordinates'][0]]
        return {
            'head': f"{edge_out['segment_id']}_t",
            'tail': f"{edge_in['segment_id']}_h",
            'coordinates': coordinates,
            'weight': ug.MANOEUVRE_PENALTY[manoeuvre],
            'geometry': sh.geometry.Point(coordinates),
            'manoeuvre': manoeuvre,
                }
    else:
        return None


def get_manoeuvre_graph(
        edges: list):
    g = nx.DiGraph()

    for e in edges:
        tail = str(e['segment_id']) + '_t'
        head = str(e['segment_id']) + '_h'
        
        g.add_edge(
            tail,
            head,
            weight=0,
            edge_id=e['segment_id'],
            geometry=e['geometry'],
            coordinates=e['coordinates'],
            manoeuvre='go_straight',
            type='segment'
            )
        attributes = {
            head: {'coordinates': e['coordinates'][1]}, 
            tail: {'coordinates': e['coordinates'][0]},
            }
        nx.set_node_attributes(g, attributes)
    
    for e_in in edges:
        for e_out in edges:
            e_data = get_manoeuvre_data(e_in, e_out)
            if e_data is not None:
                g.add_edge(
                    e_data['tail'],
                    e_data['head'],
                    weight=e_data['weight'],
                    geometry=e_data['geometry'],
                    coordinates=e_data['coordinates'],
                    manoeuvre=e_data['manoeuvre'],
                    type='manoeuvre')

    connected_nodes = sorted(
        nx.strongly_connected_components(g),
        key=len,
        reverse=True)[0]
    disconnected_nodes = [
        n for n in list(g.nodes())
        if n not in connected_nodes]
    g.remove_nodes_from(disconnected_nodes)
    return g


# D. GET INVERTED GRAPH =======================================================
def get_inverted_edge(
        edge_i: dict,
        edge_j: dict):
    if edge_i['coordinates'][1] == edge_j['coordinates'][0]:
        manoeuvre = uc.get_manoeuvre(edge_i, edge_j)
        coordinates = [
            tuple([tail + (head - tail) / 2
            for tail, head in zip(*edge_i['coordinates'])]),
            tuple([tail + (head - tail) / 2
            for tail, head in zip(*edge_j['coordinates'])])]
        offset_i = grc.get_offset_coordinates(edge_i)
        offset_j = grc.get_offset_coordinates(edge_j)
        coordinates_offset = [
            tuple([tail + (head - tail) / 2
            for tail, head in zip(*offset_i)]),
            tuple([tail + (head - tail) / 2
            for tail, head in zip(*offset_j)])]

        return {'head': edge_j['segment_id'],
                'tail': edge_i['segment_id'],
                'coordinates': coordinates,
                'coordinates_offset': coordinates_offset,
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
            e_data = get_inverted_edge(edge_i, edge_j)
            if e_data is not None:
                g.add_edge(
                    e_data['tail'],
                    e_data['head'],
                    weight=e_data['weight'],
                    geometry=e_data['geometry'],
                    coordinates=e_data['coordinates'],
                    coordinates_offset=e_data['coordinates_offset'],
                    manoeuvre=e_data['manoeuvre'],
                    type='segment',
                    )
                attributes = {
                    e_data['head']: {'coordinates': e_data['coordinates'][1]}, 
                    e_data['tail']: {'coordinates': e_data['coordinates'][0]},
                    }
                nx.set_node_attributes(g, attributes)
    
    connected_nodes = sorted(
        nx.strongly_connected_components(g),
        key=len,
        reverse=True)[0]
    disconnected_nodes = [
        n for n in list(g.nodes())
        if n not in connected_nodes]
    g.remove_nodes_from(disconnected_nodes)
    return g


# D. GET RANDOM-DISTRICT GRAPH ================================================
def get_random_district_borders(
        g: nx.DiGraph,
        district_size: list = ug.DISTRICT_SIZE):

    city_size = get_city_size(g)
    district_size = (
        round(city_size[0] * district_size[0]),
        round(city_size[1] * district_size[1]))

    # western border - x_min
    x_min = random.randint(0, city_size[0] - district_size[0])
    # eastern border - x_max
    x_max = x_min + district_size[0]
    # southern border - y_min
    y_min = random.randint(0, city_size[1] - district_size[1])
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
        

def get_city_size(
        g: nx.DiGraph) -> tuple:    
    coordinates = nx.get_node_attributes(g, 'coordinates')
    east_west = max([c[0] for c in coordinates.values()]) + 1
    south_north = max([c[1] for c in coordinates.values()]) + 1
    city_size = east_west, south_north
    return city_size


def get_random_district_graph(
        g: nx.DiGraph,
        district_size: list = ug.DISTRICT_SIZE,
        ) -> list:
    
    district_borders = get_random_district_borders(g, district_size)
    nodes_coordinates = nx.get_node_attributes(g, 'coordinates')
    district_g = g.copy()

    city_nodes = list(district_g.nodes())
    for n in city_nodes:
        node_coordinates = nodes_coordinates[n]
        if check_node_within_district(
            district_borders,
            node_coordinates) is False:
            district_g.remove_node(n)

    logging.info(
        f"\tdistrict borders:\n"
        f"\twest-east: {district_borders[0][0]} - {district_borders[1][0]}\n"
        f"\tsouth-north: {district_borders[0][1]} - {district_borders[1][1]}")
    return district_g
