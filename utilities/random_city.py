import random
import matplotlib.pyplot as plt

import shapely as sh
from shapely import geometry

# # CITY_SIZE = [EAST_TO_WEST, SOUTH_TO_NORTH]
# CITY_SIZE = [12, 8]
# # DISTRICT_SIZE = [EAST_TO_WEST, SOUTH_TO_NORTH]
# DISTRICT_SIZE = [12, 8]
# # FREQUENCIES = [NO_WAY, ONE_WAY_FORWARD, ONE_WAY_BACKWORD, TWO_WAY]
# FREQUENCIES = [0.2, 0.15, 0.15, 0.5]
from utilities.globals import *

random.seed(0)

# VISUALISE RANDOM CITY ========================================================
def plot_area(
        city: list):
    
    plt.figure(figsize=(12, 8))
    for segment in city:
        x, y = zip(*segment['coordinates'])
        plt.plot(x, y)
    plt.axis('off')
    plt.show

def get_area_statistics(
        city: list):

    segment_ids = [s['segment_id'] for s in city]
    n_segments = len(segment_ids)
    n_two_way_segments = len([s['segment_id']
        for s in city
        if s['segment_id']<0])
    n_one_way_segments = len([s['segment_id']
        for s in city
        if -s['segment_id'] not in segment_ids])
    
    print("{0} segments".format(n_segments))
    print("{0} one-way".format(n_one_way_segments))
    print("{0} two-way".format(n_two_way_segments))



# CREATE RANDOM CITY ===========================================================
def get_random_direction(
        frequencies: list = FREQUENCIES):

    direction = random.choices(
        [0, 1, 2, 3],
        weights=frequencies,
        k=1)[0]
    return direction

def get_segments(
        segment_id: int,
        coordinates: list,
        city_size: list = CITY_SIZE,
        frequencies: list = FREQUENCIES,
        ):

    direction = get_random_direction(frequencies)

    if ((direction == 0)
        or (coordinates[1][0] >= city_size[0])
        or (coordinates[1][1] >= city_size[1])):
        return ()
    if direction == 1:
        return ({'segment_id': segment_id,
                 'direction': direction,
                 'coordinates': coordinates,
                 'geometry': sh.geometry.LineString(coordinates)},)
    if direction == 2:
        return ({'segment_id': segment_id,
                 'direction': direction,
                 'coordinates': coordinates[::-1],
                 'geometry': sh.geometry.LineString(coordinates[::-1])},)
    if direction == 3:
        return ({'segment_id': segment_id,
                 'direction': direction,
                 'coordinates': coordinates,
                 'geometry': sh.geometry.LineString(coordinates)},
                {'segment_id': -segment_id,
                 'direction': direction,
                 'coordinates': coordinates[::-1],
                 'geometry': sh.geometry.LineString(coordinates[::-1])})

def get_random_city(
        city_size: list = CITY_SIZE,
        frequencies: list = FREQUENCIES,
        ) -> list:
    city = []
    segment_id = 1
    for i in range(city_size[0]):
        for j in range(city_size[1]):
            segments = get_segments(
                segment_id,
                [(i, j), (i+1, j)],
                city_size,
                frequencies,
                )
            for s in segments:
                city.append(s)
            segment_id += 1

            segments = get_segments(
                segment_id,
                [(i, j), (i, j+1)],
                city_size,
                frequencies,
                )
            for s in segments:
                city.append(s)
            segment_id += 1

    return city


# SELECT RANDOM DISTRICT =======================================================
def get_random_district_borders(
    city_size: list = CITY_SIZE,
    district_size: list = DISTRICT_SIZE):
    
    western_border = random.randint(0, city_size[0]-district_size[0])
    eastern_border = western_border + district_size[0]
    southern_border = random.randint(0, city_size[1]-district_size[1])
    nothern_border = southern_border + district_size[1]
    district_borders = [(western_border, southern_border),
        (eastern_border, nothern_border)]
    return district_borders


def check_segment_within_district(
    district_borders: list,
    segment_coordinates: list):
    for c in segment_coordinates:
        if ((c[0] < district_borders[0][0])
            or (c[0] > district_borders[1][0])
            or (c[1] < district_borders[0][1])
            or (c[1] > district_borders[1][1])):
            return False
    else:
        return True
    return district_borders


def select_random_district(
        city: list,
        city_size: list = CITY_SIZE,
        district_size: list = DISTRICT_SIZE,
        ) -> list:

    district_borders = get_random_district_borders(city_size, district_size)

    random_district = []
    for segment in city:
        if check_segment_within_district(
            district_borders,
            segment['coordinates']) is True:
            random_district.append(segment)
    return random_district