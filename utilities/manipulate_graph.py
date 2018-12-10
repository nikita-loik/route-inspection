import sys

import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import shapely as sh

from utilities.globals import *


# ==============================================================================
def condence_nodes(
    g: nx.DiGraph,
    nodes_to_condence: list,
    new_node: str,
    coordinates: tuple):
#     https://gist.github.com/Zulko/7629206
    
    g.add_node(new_node, coordinates=coordinates) # Add the condensation node
    
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


# GRAPH GRAFTING ===============================================================
