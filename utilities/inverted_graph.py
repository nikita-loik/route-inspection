import sys

import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import shapely as sh

from utilities.globals import *


# CONVERT segment segmentS TO INVERTED GRAPH ====================================
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
                'weight': get_manoeuvre_penalty(manoeuvre),
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

                g.node[edge_data['head']]['coordinates'] = edge_data['coordinates'][1]
                g.node[edge_data['tail']]['coordinates'] = edge_data['coordinates'][0]
    return g