import numpy as np

# RANDOM CITY PARAMETERS =======================================================
CITY_SIZE = (24, 16)
DISTRICT_SIZE = (12, 8)
# FREQUENCIES = {
# 'no_way': .2,
# 'one_way_direct': .15,
# 'one_way_reverse': .15,
# 'two_way': .5}
FREQUENCIES = [0.2, 0.15, 0.15, 0.5]

# ROUTE PARAMETERS =============================================================

MANOEUVRE_PENALTY = {
    'make_u_turn': 10,
    'turn_left': 3,
    'turn_right': 0,
    'go_straight': 0}

