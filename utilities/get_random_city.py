import random
import matplotlib.pyplot as plt

import shapely as sh
from shapely import geometry

import utilities.globals as g_globals

random.seed(0)

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(asctime)s: %(filename)s: %(lineno)s:\n%(message)s")
logger = logging.getLogger(__name__)


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
    
    logger.info(
        f"\t{n_segments} segments\n"
        f"\t{n_one_way_segments} one-way\n"
        f"\t{n_two_way_segments} two-way\n")



# CREATE RANDOM CITY ===========================================================
def get_random_direction(
        frequencies: list = g_globals.FREQUENCIES):

    direction = random.choices(
        [0, 1, 2, 3],
        weights=frequencies,
        k=1)[0]
    return direction

def get_segments(
        segment_id: int,
        coordinates: list,
        city_size: list = g_globals.CITY_SIZE,
        frequencies: list = g_globals.FREQUENCIES,
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
        city_size: list = g_globals.CITY_SIZE,
        frequencies: list = g_globals.FREQUENCIES,
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
    get_area_statistics(city)
    return city