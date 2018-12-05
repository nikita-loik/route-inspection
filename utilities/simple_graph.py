import matplotlib.pyplot as plt
import networkx as nx


# CONVERT STREET SEGMENTS TO GRAPH =============================================
def get_crossroads_dictionary(
        street_segments: list):
    segments_coordinates = [segment['coordinates']
        for segment in street_segments]
    sorted_coordinates = sorted(list(set([c
        for coordinates in segments_coordinates
        for c in coordinates])))
    crossroads = {c: sorted_coordinates.index(c)
        for c in sorted_coordinates}
    return crossroads


def get_city_graph(
        street_segments: list):
    g = nx.DiGraph()
    
    crossroads = get_crossroads_dictionary(street_segments)
    for segment in street_segments:
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
    return g

# VISUALISE CITY GRAPH =========================================================

def visualise_city_graph(
        g: nx.DiGraph):
    nodes_coordinates = nx.get_node_attributes(g, 'coordinates')
    
    g_statistics = get_city_graph_statistics(g)
    dead_ends = g_statistics['dead_ends']
    disconnected_nodes = g_statistics['disconnected_nodes']
    
    plt.figure(figsize=(16, 12))
    nx.draw_networkx_nodes(g, nodes_coordinates, node_size=20, node_color="black")
    nx.draw_networkx_edges(g, nodes_coordinates, alpha=0.5)
    for n in dead_ends:
        plt.scatter(n[0], n[1], s=500, c="grey", alpha=0.3)
    for n in disconnected_nodes:
        plt.scatter(n[0], n[1], s=500, c="red", alpha=0.3)
    plt.axis('off')
    plt.title('')
    plt.show()

    
def get_city_graph_statistics(
        g: nx.DiGraph):
    
    nodes_coordinates = nx.get_node_attributes(g, 'coordinates')
    dead_ends = []
    for n in g.nodes:
        if ((g.in_degree(n) == 1)
            and (g.out_degree(n) == 1)):
            dead_ends.append(nodes_coordinates[n])
            
    connected_nodes = sorted(nx.strongly_connected_components(g),
                                                   key=len,
                                                   reverse=True)[0]
    disconnected_nodes = [nodes_coordinates[n]
                          for n in list(g.nodes())
                          if n not in connected_nodes]
    dead_ends = [n for n in dead_ends if n not in disconnected_nodes]
    
    print("{0} dead ends".format(len(dead_ends)))
    print("{0} disconnected nodes".format(len(disconnected_nodes)))
    return{'dead_ends':dead_ends,
           'disconnected_nodes':disconnected_nodes}