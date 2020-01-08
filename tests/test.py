import os, sys, inspect

import numpy as np

import matplotlib
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')

import networkx as nx
import shapely as sh

working_dir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(working_dir)
sys.path.insert(0, parent_dir)

from utilities import global_parameters as gp
from utilities import common as uc
from utilities import get_random_city as grc
from utilities import get_graph as gg
from utilities import forge_graph as fg
from utilities import visualise_graph as vg
from utilities import get_route as gr

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(asctime)s: %(filename)s: %(lineno)s:\n%(message)s")
logger = logging.getLogger(__name__).setLevel(logging.DEBUG)


# def test_get_random_city():

#     city_size=ug.CITY_SIZE
#     frequencies=ug.FREQUENCIES
#     random_city = grc.get_random_city(
#         city_size=city_size,
#         frequencies=frequencies,
#         )

#     x, y = city_size
#     max_n_segments =  x * (y - 1) + (x - 1) * y
#     no_way, one_way_direct, one_way_reverse, two_way = frequencies
#     one_way = one_way_direct + one_way_reverse

#     n_segments_limit = np.ceil(2 * max_n_segments * (1 - no_way))
#     n_one_way_limit = np.ceil(max_n_segments * one_way)
#     n_two_way_limit = np.ceil(max_n_segments * two_way)

#     area_statistics = grc.get_area_statistics(random_city)

#     assert area_statistics['n_segments'] < n_segments_limit
#     assert area_statistics['n_one_way_segments'] < n_one_way_limit
#     assert area_statistics['n_two_way_segments'] < n_two_way_limit


def test_get_random_city():
    '''
    Test get_random_city ignoring randomness.
    '''
    city_size=gp.CITY_SIZE
    frequencies=[0., 0., 0., 1.]
    random_city = grc.get_random_city(
        city_size=city_size,
        frequencies=frequencies,
        )

    x, y = city_size
    max_n_segments =  x * (y - 1) + (x - 1) * y

    area_statistics = grc.get_area_statistics(random_city)

    assert(area_statistics['n_segments'] == max_n_segments * 2)
    assert(area_statistics['n_one_way_segments'] == 0)
    assert(area_statistics['n_two_way_segments'] == max_n_segments)


class TestGraphAndRoute:
    def get_graph_and_route_statistics(
            self,
            city_size:list,
            frequencies:list):
        random_city = grc.get_random_city(
            city_size = city_size,
            frequencies = frequencies,
            )
        inverted_g = gg.get_inverted_graph(random_city)

        inverted_g = fg.prune_u_turns(inverted_g)
        inverted_g = fg.prune_left_turns(inverted_g)

        graph_statistics = vg.get_graph_statistics(inverted_g)

        virtual_g = inverted_g.copy()
        virtual_g = fg.balance_graph_iteratively(inverted_g)
        virtual_circuit = gr.get_virtual_path(virtual_g)
        real_circuit = gr.get_real_path(
            virtual_circuit,
            inverted_g,
            virtual_g)
        eulerian_circuit_len = len(real_circuit['circuit_by_node'])

        return {
            'n_nodes': len(inverted_g.nodes()),
            'n_edges': len(inverted_g.edges()),
            'strongly_connected': nx.is_strongly_connected(inverted_g),
            'n_disconnected_nodes': len(graph_statistics['disconnected_nodes']),
            'n_straight_drives': len(graph_statistics['straight_drives']),
            'n_right_turns': len(graph_statistics['right_turns']),
            'n_left_turns': len(graph_statistics['left_turns']),
            'n_u_turns': len(graph_statistics['u_turns']),
            'n_dead_ends': len(graph_statistics['dead_ends']),
            'eulerian_circuit_len': eulerian_circuit_len
            }

    def test_get_route_city_size_2_1(self):
        graph_and_route_statistics = self.get_graph_and_route_statistics(
            city_size = [2, 1],
            frequencies = [0, 0, 0, 1],
            )
        test_statistics = {
            'n_nodes': 2,
            'n_edges': 2,
            'strongly_connected': True,
            'n_disconnected_nodes': 0,
            'n_straight_drives': 0,
            'n_right_turns': 0,
            'n_left_turns': 0,
            'n_u_turns': 2,
            'n_dead_ends': 2,
            'eulerian_circuit_len': 2}
        for k in test_statistics.keys():
            assert graph_and_route_statistics[k] == test_statistics[k]
        
    def test_get_route_city_size_2_2(self):
        graph_and_route_statistics = self.get_graph_and_route_statistics(
            city_size = [2, 2],
            frequencies = [0, 0, 0, 1],
            )
        test_statistics = {
            'n_nodes': 8,
            'n_edges': 10,
            'strongly_connected': True,
            'n_disconnected_nodes': 0,
            'n_straight_drives': 0,
            'n_right_turns': 4,
            'n_left_turns': 4,
            'n_u_turns': 2,
            'n_dead_ends': 0,
            'eulerian_circuit_len': 16}
        for k in test_statistics.keys():
            assert graph_and_route_statistics[k] == test_statistics[k]

    # def test_get_route_city_size_3_1(self):
    #     graph_and_route_statistics = self.get_graph_and_route_statistics(
    #         city_size = [3, 2],
    #         frequencies = [0, 0, 0, 1],
    #         )
    #     test_statistics = {
    #         'n_nodes': 4,
    #         'n_edges': 4,
    #         'strongly_connected': True,
    #         'n_disconnected_nodes': 0,
    #         'n_straight_drives': 2,
    #         'n_right_turns': 0,
    #         'n_left_turns': 0,
    #         'n_u_turns': 4,
    #         'n_dead_ends': 0,
    #         'eulerian_circuit_len': 4}
    #     for k in test_statistics.keys():
    #         assert graph_and_route_statistics[k] == test_statistics[k]

    def test_get_route_city_size_3_2(self):
        graph_and_route_statistics = self.get_graph_and_route_statistics(
            city_size = [3, 2],
            frequencies = [0, 0, 0, 1],
            )
        test_statistics = {
            'n_nodes': 14,
            'n_edges': 18,
            'strongly_connected': True,
            'n_disconnected_nodes': 0,
            'n_straight_drives': 4,
            'n_right_turns': 8,
            'n_left_turns': 6,
            'n_u_turns': 0,
            'n_dead_ends': 0,
            'eulerian_circuit_len': 24}
        for k in test_statistics.keys():
            assert graph_and_route_statistics[k] == test_statistics[k]