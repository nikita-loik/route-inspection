import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import shapely as sh


# CONVERT STREET SEGMENTS TO GRAPH =============================================
def get_manoeuvre_penalty(
        manoeuvre: str):
    manoeuvre_penalty = {'make_u_turn': 10,
                         'turn_left': 3,
                         'turn_right': 0,
                         'go_straight': 0}
    return manoeuvre_penalty[manoeuvre]


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
    # print(angle)
    
    if 30 < angle <= 175:
#         print("turn right {0:.0f}".format(angle))
        return 'turn_right'
    elif 175 < angle <= 185:
#         print("go straight {0:.0f}".format(angle))
        return 'make_u_turn'
    elif 185 < angle <= 330:
#         print("turn left {0:.0f}".format(angle))
        return 'turn_left'
    elif (330 < angle) or (angle <= 30):
#         print("U-turn {0:.0f}".format(angle))
        return 'go_straight'


# def get_manoeuvre_data(
#         i_segment: dict,
#         j_segment: dict,
#         manoeuvre: str):
    
#     # if i_segment['coordinates'][0] == j_segment['coordinates'][1]:
#     #     tail = str(j_segment['segment_id']) + '_h'
#     #     head = str(i_segment['segment_id']) + '_t'
#     #     coordinates = i_segment['coordinates'][0]

#     elif i_segment['coordinates'][1] == j_segment['coordinates'][0]:
#         tail = str(i_segment['segment_id']) + '_h'
#         head = str(j_segment['segment_id']) + '_t'
#         coordinates = i_segment['coordinates'][1]
            
#     return {'head': head,
#             'tail': tail,
#             'coordinates': coordinates,
#             'weight': get_manoeuvre_penalty(manoeuvre),
#             'geometry': sh.geometry.Point(coordinates),
#             'manoeuvre': manoeuvre}


def get_manoeuvre_edge(
        i_segment: dict,
        j_segment: dict):
    # if ((i_segment['coordinates'][0] == j_segment['coordinates'][1]) or
    #         (i_segment['coordinates'][1] == j_segment['coordinates'][0])):
    if i_segment['coordinates'][1] == j_segment['coordinates'][0]:
        manoeuvre = get_manoeuvre(i_segment, j_segment)
        coordinates = i_segment['coordinates'][1]
        return {'head': str(j_segment['segment_id']) + '_t',
                'tail': str(i_segment['segment_id']) + '_h',
                'coordinates': coordinates,
                'weight': get_manoeuvre_penalty(manoeuvre),
                'geometry': sh.geometry.Point(coordinates),
                'manoeuvre': manoeuvre}

        # return get_manoeuvre_data(i_segment, j_segment, manoeuvre)
    else:
        return None


def get_manoeuvre_graph(
        street_segments: list):
    g = nx.DiGraph()
    
    for segment in street_segments:
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
    
    for i, i_segment in enumerate(street_segments):
        # for j_segment in street_segments[i+1:]:
        for j_segment in street_segments:
            edge_data = get_manoeuvre_edge(i_segment, j_segment)
            if edge_data is not None:
                g.add_edge(
                    edge_data['tail'],
                    edge_data['head'],
                    weight=edge_data['weight'],
                    geometry=edge_data['geometry'],
                    coordinates=edge_data['coordinates'],
                    manoeuvre=edge_data['manoeuvre'])
    return g


# VISUALISE CITY GRAPH =========================================================
def visualise_manoeuvre_graph(
        g: nx.DiGraph):
    nodes_coordinates = nx.get_node_attributes(g, 'coordinates')
    
    g_statistics = get_manoeuvre_graph_statistics(g)
    dead_ends = g_statistics['dead_ends']
    disconnected_nodes = g_statistics['disconnected_nodes']
    
    plt.figure(figsize=(16, 12))
    nx.draw_networkx_nodes(g, nodes_coordinates, node_size=20, node_color="black")
    nx.draw_networkx_edges(g, nodes_coordinates, alpha=0.5)
    for n in dead_ends:
        plt.scatter(n[0], nodes_coordinates[n][1], s=500, c="grey", alpha=0.3)
    for n in disconnected_nodes:
        plt.scatter(n[0], n[1], s=500, c="red", alpha=0.3)
    plt.axis('off')
    plt.title('')
    plt.show()

    
def get_manoeuvre_graph_statistics(
        g: nx.DiGraph):
    
    nodes_coordinates = nx.get_node_attributes(g, 'coordinates')
    dead_ends = []

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
    
    print("{0} dead ends".format(len(dead_ends)))
    print("{0} disconnected nodes".format(len(disconnected_nodes)))
    print("{0} right turns".format(len(right_turns)))
    print("{0} left turns".format(len(left_turns)))
    print("{0} u-turns".format(len(u_turns)))
    return{'dead_ends':dead_ends,
           'disconnected_nodes':disconnected_nodes}