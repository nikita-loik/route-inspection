import numpy as np


# RANDOM CITY PARAMETERS =======================================================
CITY_SIZE = [12, 8]
DISTRICT_SIZE = [12, 8]
FREQUENCIES = [0.2, 0.5, 0.15, 0.15]


# GRAPH GENERATION =============================================================
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

# ROUTE PARAMETERS =============================================================
def get_manoeuvre_penalty(
        manoeuvre: str):
    manoeuvre_penalty = {'make_u_turn': 10,
                         'turn_left': 3,
                         'turn_right': 0,
                         'go_straight': 0}
    return manoeuvre_penalty[manoeuvre]

