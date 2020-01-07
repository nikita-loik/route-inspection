import sys

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')
import networkx as nx
import shapely as sh

import utilities.globals as ug
import utilities.get_random_city as grc

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(asctime)s: %(filename)s: %(lineno)s:\n%(message)s")
logger = logging.getLogger(__name__)


# PLOTTING FUNCTIONS ==========================================================
def plot_arrow(
    coordinates: list,
    color: str = 'gray'):
    x, y = coordinates[0]
    x_end, y_end = coordinates[1]
    dx = x_end - x
    dy = y_end - y
    plt.arrow(
        x=x, y=y,
        dx=dx, dy=dy,
        length_includes_head=True,
        shape='left',
        head_width=.13,
        head_length=.13,
        facecolor=color,
        edgecolor=color,
        width=.07)


# A. visualise naive graph ====================================================
def visualise_naive_graph(
        g: nx.DiGraph):
    nodes_coordinates = nx.get_node_attributes(g, 'coordinates')
    x_min = min([nc[0] for nc in nodes_coordinates.values()])
    x_max = max([nc[0] for nc in nodes_coordinates.values()])
    y_min = min([nc[1] for nc in nodes_coordinates.values()])
    y_max = max([nc[1] for nc in nodes_coordinates.values()])

    g_statistics = get_naive_graph_statistics(g)
    dead_ends = g_statistics['dead_ends']
    disconnected_nodes = g_statistics['disconnected_nodes']

    fig, ax = plt.subplots(1, 1, figsize=ug.FIGURE_SIZE)
    for e in g.edges:
        e_coordinates = g.get_edge_data(*e)
        offset_coordinates = grc.get_offset_coordinates(e_coordinates)
        # Plot arrow for every edge.
        plot_arrow(offset_coordinates)
    # Highlight dead-ends.
    for n in dead_ends:
        plt.scatter(
            *nodes_coordinates[n],
            s=500,
            c="grey",
            alpha=0.3)
    # Highlight disconnected nodes.
    for n in disconnected_nodes:
        plt.scatter(
            *nodes_coordinates[n],
            s=500,
            c="red",
            alpha=0.3)
    # Add node ids to graph.
    # for n in g.nodes():
    #     plt.text(
    #         nodes_coordinates[n][0] + 0.1,
    #         nodes_coordinates[n][1] + 0.1,
    #         n,
    #         color='r')
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

    
def get_naive_graph_statistics(
        g: nx.DiGraph):
    
    nodes_coordinates = nx.get_node_attributes(g, 'coordinates')
    dead_ends = []
    for n in g.nodes:
        if ((g.in_degree(n) >= 1)
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
        f"\tnodes #: {len(g.nodes())}\n"
        f"\tedges #: {len(g.edges())}\n"
        f"\tstrongly connected: {nx.is_strongly_connected(g)}\n"
        f"\tdisconnected nodes: {len(set(disconnected_nodes_coordinates))}"
        f"\tdead ends:{len(set(dead_ends_coordinates))}\n")

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
    # print(nodes_coordinates)
    x_min = min([nc[0] for nc in nodes_coordinates.values()])
    x_max = max([nc[0] for nc in nodes_coordinates.values()])
    y_min = min([nc[1] for nc in nodes_coordinates.values()])
    y_max = max([nc[1] for nc in nodes_coordinates.values()])
    
    g_statistics = get_manoeuvre_graph_statistics(g)
    dead_ends = g_statistics['dead_ends']
    disconnected_nodes = g_statistics['disconnected_nodes']
    
    fig, ax = plt.subplots(1, 1, figsize=ug.FIGURE_SIZE)
    for e in g.edges:
        try:
            e_data = g.get_edge_data(*e)
            # print(e_data)
            if e_data['type'] == 'segment':
                offset_coordinates = grc.get_offset_coordinates(e_data)
                # print(offset_coordinates)
                plot_arrow(offset_coordinates)
        except ValueError:
            pass
    for n in dead_ends:
        plt.scatter(
            nodes_coordinates[n][0],
            nodes_coordinates[n][1],
            s=500,
            c="grey",
            alpha=0.3)
    for n in disconnected_nodes:
        plt.scatter(n[0], n[1], s=500, c="red", alpha=0.3)
    # Label nodes.
    # for n in g.nodes():
    #     x_coordinate = nodes_coordinates[n][0] + 0.1
    #     if n.endswith('t'):
    #         y_coordinate = nodes_coordinates[n][1] - 0.1
    #     else:
    #         y_coordinate = nodes_coordinates[n][1] + 0.1
    #     plt.text(
    #         x_coordinate,
    #         y_coordinate,
    #         n,
    #         color='r',
    #         # size=10,
    #         )
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

    dead_ends = []
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
    f"\tnodes #: {len(g.nodes())}\n"
    f"\tedges #: {len(g.edges())}\n"
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


# C. visualise inverted graph =================================================
def visualise_inverted_graph(
        inverted_g: nx.DiGraph,
        manoeuvre_g: nx.DiGraph
        ):

    fig, ax = plt.subplots(1, 1, figsize=ug.FIGURE_SIZE)

    # Plot inverted graph.
    nodes_coordinates_inverted_g = nx.get_node_attributes(
        inverted_g,
        'coordinates')
    statistics_inverted_g = get_manoeuvre_graph_statistics(inverted_g)
    dead_ends_inverted_g = statistics_inverted_g['dead_ends']
    disconnected_nodes_inverted_g = statistics_inverted_g['disconnected_nodes']
    for e in inverted_g.edges:
        try:
            e_data = inverted_g.get_edge_data(*e)
            plot_arrow(e_data['coordinates_offset'], color='red')
        except ValueError:
            pass
    for n in dead_ends_inverted_g:
        plt.scatter(
            nodes_coordinates_inverted_g[n][0],
            nodes_coordinates_inverted_g[n][1],
            s=500,
            c="grey",
            alpha=0.3)
    for n in disconnected_nodes_inverted_g:
        plt.scatter(n[0], n[1], s=500, c="red", alpha=0.3)

    # Plot manoeuvre graph.
    nodes_coordinates_manoeuvre_g = nx.get_node_attributes(
        manoeuvre_g,
        'coordinates')
    statistics_manoeuvre_g= get_manoeuvre_graph_statistics(manoeuvre_g)
    dead_ends_manoeuvre_g = statistics_manoeuvre_g['dead_ends']
    disconnected_nodes_manoeuvre_g = statistics_manoeuvre_g['disconnected_nodes']
    
    for e in manoeuvre_g.edges:
        try:
            e_data = manoeuvre_g.get_edge_data(*e)
            if e_data['type'] == 'segment':
                offset_coordinates = grc.get_offset_coordinates(e_data)
                plot_arrow(offset_coordinates)
        except ValueError:
            pass
    for n in dead_ends_manoeuvre_g:
        plt.scatter(
            nodes_coordinates_manoeuvre_g[n][0],
            nodes_coordinates_manoeuvre_g[n][1],
            s=500,
            c="grey",
            alpha=0.3)
    for n in disconnected_nodes_manoeuvre_g:
        plt.scatter(n[0], n[1], s=500, c="red", alpha=0.3)

    # Set plot parameters.
    x_min = min([nc[0] for nc in nodes_coordinates_inverted_g.values()])
    x_max = max([nc[0] for nc in nodes_coordinates_inverted_g.values()])
    y_min = min([nc[1] for nc in nodes_coordinates_inverted_g.values()])
    y_max = max([nc[1] for nc in nodes_coordinates_inverted_g.values()])

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
