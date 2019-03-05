import sys

import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import shapely as sh

import utilities.globals as g_globals

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(asctime)s: %(filename)s: %(lineno)s:\n%(message)s")
logger = logging.getLogger(__name__)


# A. visualise city graph =====================================================

def visualise_city_graph(
        g: nx.DiGraph):
    nodes_coordinates = nx.get_node_attributes(g, 'coordinates')
    x_min = min([nc[0] for nc in nodes_coordinates.values()])
    x_max = max([nc[0] for nc in nodes_coordinates.values()])
    y_min = min([nc[1] for nc in nodes_coordinates.values()])
    y_max = max([nc[1] for nc in nodes_coordinates.values()])

    # logger.info(f"{x_min}\n{x_max}\n{y_min}\n{y_max}")

    g_statistics = get_city_graph_statistics(g)
    dead_ends = g_statistics['dead_ends']
    disconnected_nodes = g_statistics['disconnected_nodes']

    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    nx.draw_networkx_nodes(
        g,
        nodes_coordinates,
        node_size=20,
        node_color="black")
    nx.draw_networkx_edges(g, nodes_coordinates, alpha=0.5)
    for n in dead_ends:
        plt.scatter(*nodes_coordinates[n], s=500, c="grey", alpha=0.3)
    for n in disconnected_nodes:
        plt.scatter(*nodes_coordinates[n], s=500, c="red", alpha=0.3)
    # plt.axis('off')
    plt.xticks(np.arange(x_min, x_max + 1.0, 1), fontsize=14)
    plt.yticks(np.arange(y_min, y_max + 1.0, 1), fontsize=14)
    ax.set_xlim(x_min - 1, x_max + 1)
    ax.set_ylim(y_min - 1, y_max + 1)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    plt.title('')
    plt.show()

    
def get_city_graph_statistics(
        g: nx.DiGraph):
    
    nodes_coordinates = nx.get_node_attributes(g, 'coordinates')
    dead_ends = []
    for n in g.nodes:
        if ((g.in_degree(n) == 1)
            and (g.out_degree(n) == 1)):
            dead_ends.append(n)
            
    connected_nodes = sorted(nx.strongly_connected_components(g),
                                                   key=len,
                                                   reverse=True)[0]
    disconnected_nodes = [n
                          for n in list(g.nodes())
                          if n not in connected_nodes]
    disconnected_nodes_coordinates = [
        nodes_coordinates[n]
        for n in disconnected_nodes]
    dead_ends = [n for n in dead_ends
        if n not in disconnected_nodes]
    dead_ends_coordinates = [
        nodes_coordinates[n]
        for n in dead_ends]

    logger.info(
        f"\t{len(set(dead_ends_coordinates))} dead ends\n"
        f"\t{len(set(disconnected_nodes_coordinates))} disconnected nodes")
    # logger.info(
    #     f"\t{len(dead_ends)} dead ends\n"
    #     f"\t{len(disconnected_nodes)} disconnected nodes")
    return{
        'dead_ends':dead_ends,
        'disconnected_nodes':disconnected_nodes,
        'dead_ends_coordinates': dead_ends_coordinates,
        'disconnected_nodes_coordinates': disconnected_nodes_coordinates,
        }


# B. visualise manoeuvre graph ================================================
def visualise_manoeuvre_graph(
        g: nx.DiGraph):
    nodes_coordinates = nx.get_node_attributes(g, 'coordinates')
    x_min = min([nc[0] for nc in nodes_coordinates.values()])
    x_max = max([nc[0] for nc in nodes_coordinates.values()])
    y_min = min([nc[1] for nc in nodes_coordinates.values()])
    y_max = max([nc[1] for nc in nodes_coordinates.values()])
    
    g_statistics = get_manoeuvre_graph_statistics(g)
    dead_ends = g_statistics['dead_ends']
    disconnected_nodes = g_statistics['disconnected_nodes']
    
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    nx.draw_networkx_nodes(
        g,
        nodes_coordinates,
        node_size=20,
        node_color="black")
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
    # plt.axis('off')
    plt.xticks(np.arange(x_min, x_max + 1, 1), fontsize=14)
    plt.yticks(np.arange(y_min, y_max + 1, 1), fontsize=14)
    ax.set_xlim(x_min - 1, x_max + 1)
    ax.set_ylim(y_min - 1, y_max + 1)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    plt.title('')
    plt.show()

    
def get_manoeuvre_graph_statistics(
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
    logger.info(
    f"\tstrongly connected: {nx.is_strongly_connected(g)}\n"
    f"\tdisconnected nodes: {len(disconnected_nodes)}\n"
    f"\tstraight drives: {len(straight_drives)}\n"
    f"\tright turns: {len(right_turns)}\n"
    f"\tleft turns: {len(left_turns)}\n"
    f"\tu-turns: {len(u_turns)}\n"
    f"\tdead ends: {len(dead_ends)}"
    )

    return{'dead_ends':dead_ends,
           'disconnected_nodes':disconnected_nodes}

