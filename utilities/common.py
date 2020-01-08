import os, sys, inspect
import numpy as np

working_dir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(working_dir)
sys.path.insert(0, parent_dir)

from utilities import global_parameters as gp
from utilities import get_random_city as grc
from utilities import get_graph as gg
from utilities import forge_graph as fg
from utilities import visualise_graph as vg
from utilities import get_route as gr


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