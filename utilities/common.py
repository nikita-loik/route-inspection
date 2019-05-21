import numpy as np


def get_angle_between_two_edges(
        edge_i: dict,
        edge_j: dict,
        ):
    v_i = np.array([head - tail
        for tail, head in zip(*edge_i['coordinates'])])
    v_j = np.array([head - tail
        for tail, head in zip(*edge_j['coordinates'])])

    cosine = np.vdot(v_i, v_j) / (np.linalg.norm(v_i) * np.linalg.norm(v_j))
    determinant = np.linalg.det([v_i, v_j])
    if determinant < 0:
        angle = 180 * np.arccos(cosine) / np.pi
    else:
        angle = 360 - (180 * np.arccos(cosine) / np.pi)
    
    return angle

def get_manoeuvre(
        edge_i: dict,
        edge_j: dict):

    angle = get_angle_between_two_edges(
        edge_i, edge_j)
    
    if 30 < angle <= 175:
        return 'turn_right'
    elif 175 < angle <= 185:
        return 'make_u_turn'
    elif 185 < angle <= 330:
        return 'turn_left'
    elif (330 < angle) or (angle <= 30):
        return 'go_straight'