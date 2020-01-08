import numpy as np

# RANDOM CITY PARAMETERS =======================================================
CITY_SIZE = (24, 16)
DISTRICT_SIZE = (.5, .5)

# FREQUENCIES (no_way, one_way_direct, one_way_reverse, two_way)
FREQUENCIES = (.2, .15, .15, .5)

# ROUTE PARAMETERS =============================================================

MANOEUVRE_PENALTY = {
    'make_u_turn': 10,
    'turn_left': 3,
    'turn_right': 0,
    'go_straight': 0}

FIGURE_SIZE = (12, 8)