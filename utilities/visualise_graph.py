import sys

import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import shapely as sh

from utilities.globals import *

# VISUALISE MANOEUVRE GRAPH ====================================================
def visualise_graph(
        g: nx.DiGraph):
    nodes_coordinates = nx.get_node_attributes(g, 'coordinates')
    
    g_statistics = get_graph_statistics(g)
    dead_ends = g_statistics['dead_ends']
    disconnected_nodes = g_statistics['disconnected_nodes']
    
    plt.figure(figsize=(16, 12))
    nx.draw_networkx_nodes(g, nodes_coordinates, node_size=20, node_color="black")
    nx.draw_networkx_edges(g, nodes_coordinates, alpha=0.5)
    for n in dead_ends:
        plt.scatter(
            nodes_coordinates[n][0],
            nodes_coordinates[n][1],
            s=500,
            c="grey",
            alpha=0.3)
    for n in disconnected_nodes:
        plt.scatter(n[0], n[1], s=500, c="red", alpha=0.3)
    plt.axis('off')
    plt.title('')
    plt.show()

    
def get_graph_statistics(
        g: nx.DiGraph):
    
    nodes_coordinates = nx.get_node_attributes(g, 'coordinates')
    dead_ends = []

    straight_drives = [g.get_edge_data(*e)
        for e in g.edges()
        if g.get_edge_data(*e)['manoeuvre']=='go_straight']
    right_turns = [g.get_edge_data(*e)
        for e in g.edges()
        if g.get_edge_data(*e)['manoeuvre']=='turn_right']
    left_turns = [g.get_edge_data(*e)
        for e in g.edges()
        if g.get_edge_data(*e)['manoeuvre']=='turn_left']
    u_turns = [g.get_edge_data(*e)
        for e in g.edges()
        if g.get_edge_data(*e)['manoeuvre']=='make_u_turn']


    for n in g.nodes:
        if ((g.in_degree(n) == 1)
                and (g.out_degree(n) == 1)):
            out_edge = list(g.out_edges(n))[0]
            manoeuvre = g.get_edge_data(*out_edge)['manoeuvre']
            if manoeuvre == 'make_u_turn':
                dead_ends.append(n)
            
    connected_nodes = sorted(nx.strongly_connected_components(g),
                                                   key=len,
                                                   reverse=True)[0]
    disconnected_nodes = [nodes_coordinates[n]
                          for n in list(g.nodes())
                          if n not in connected_nodes]
    dead_ends = [n for n in dead_ends if n not in disconnected_nodes]
    
    print("{0} disconnected nodes".format(len(disconnected_nodes)))
    print("{0} straight drives".format(len(straight_drives)))
    print("{0} right turns".format(len(right_turns)))
    print("{0} left turns".format(len(left_turns)))
    print("{0} u-turns".format(len(u_turns)))
    print("{0} dead ends".format(len(dead_ends)))
    return{'dead_ends':dead_ends,
           'disconnected_nodes':disconnected_nodes}