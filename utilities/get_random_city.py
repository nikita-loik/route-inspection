import random
import numpy as np

import matplotlib
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')

import shapely as sh
from shapely import geometry

import utilities.globals as ug

random.seed(0)

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(asctime)s: %(filename)s: %(lineno)s:\n%(message)s")
logger = logging.getLogger(__name__)


# VISUALISE RANDOM CITY =======================================================
def get_offset_coordinates(
        segment: dict) -> list:
    s_linestring = sh.geometry.LineString(
        segment['coordinates'])
    s_offset = s_linestring.parallel_offset(
        distance=.1,
        side='right')
    s_scaled = sh.affinity.scale(
        s_offset,
        xfact=0.8,
        yfact=0.8,
        origin='center')
    coordinates_offset = list(s_scaled.coords)
    return coordinates_offset

def plot_area(
        segments: list):

    points = list(set([p for s in segments for p in s['coordinates']]))

    x_min = min([p[0] for p in points])
    x_max = max([p[0] for p in points])
    y_min = min([p[1] for p in points])
    y_max = max([p[1] for p in points])
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    for s in segments:
        # x, y = zip(*s['coordinates'])
        # print(s)
        s_coordinates = get_offset_coordinates(s)
        x, y = zip(*s_coordinates)
        plt.plot(x, y, c='gray')
    plt.xticks(np.arange(x_min, x_max + 1.0, 1), fontsize=14)
    plt.yticks(np.arange(y_min, y_max + 1.0, 1), fontsize=14)
    ax.set_xlim(x_min - 1, x_max + 1)
    ax.set_ylim(y_min - 1, y_max + 1)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    # plt.axis('off')
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
        f"\t{n_two_way_segments} two-way")



# GET RANDOM CITY =============================================================
def get_random_direction(
        frequencies: list = ug.FREQUENCIES):
    # directions:
    # 0 — no_way
    # 1 — one_way_direct
    # 2 — one_way_reverse
    # 3 — two_way
    direction = random.choices(
        [0, 1, 2, 3],
        weights=frequencies,
        k=1)[0]
    return direction

def get_segments(
        segment_id: int,
        coordinates: list,
        city_size: tuple = ug.CITY_SIZE,
        frequencies: list = ug.FREQUENCIES,
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

    # if ((direction == 0)
    #     or (coordinates[1][0] >= city_size[0])
    #     or (coordinates[1][1] >= city_size[1])):
    #     return ()
    # if direction == 1:
    #     geometry = sh.geometry.LineString(
    #         coordinates).parallel_offset(0.1)
    #     return ({'segment_id': segment_id,
    #              'direction': direction,
    #              'coordinates': list(geometry.coords),
    #              'geometry': geometry},)
    # if direction == 2:
    #     geometry = sh.geometry.LineString(
    #         coordinates[::-1]).parallel_offset(0.1)
    #     return ({'segment_id': segment_id,
    #              'direction': direction,
    #              'coordinates': list(geometry.coords),
    #              'geometry': geometry},)
    # if direction == 3:
    #     geometry_i = sh.geometry.LineString(
    #         coordinates).parallel_offset(0.1)
    #     geometry_j = sh.geometry.LineString(
    #         coordinates[::-1]).parallel_offset(0.1)
    #     return ({'segment_id': segment_id,
    #              'direction': direction,
    #              'coordinates': list(geometry_i.coords),
    #              'geometry': geometry_i},
    #             {'segment_id': -segment_id,
    #              'direction': direction,
    #              'coordinates': list(geometry_j.coords),
    #              'geometry': geometry_j})


def get_random_city(
        city_size: tuple = ug.CITY_SIZE,
        frequencies: list = ug.FREQUENCIES,
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


def get_points_dictionary(
        segments: list
        ):
    points_coordinates = {}
    sorted_points_coordinates = sorted(
        list(set([n for e in segments for n in e['coordinates']])))
    for n in sorted_points_coordinates:
        points_coordinates[n] = sorted_points_coordinates.index(n)
    return points_coordinates


# def delete_disconnected_segments(
#         segments: list):
#     tails = [s['coordinates'][0] for s in segments]
#     heads = [s['coordinates'][1] for s in segments]

#     only_tails = []
#     for t in tails:
#         if t not in heads:
#             only_tails.append(t)

#     only_heads = []
#     for h in heads:
#         if h not in tails:
#             only_heads.append(h)

#     logger.info(
#         f"only tails: {len(only_tails)}\nonly heads: {len(only_heads)}")

#     clean_segments = []
#     for s in segments:
#         if ((s['coordinates'][0] not in only_tails)
#            and (s['coordinates'][1] not in only_heads)):
#             clean_segments.append(s)
#     return clean_segments

# GET RANDOM DISTRICT =========================================================
def get_random_district_bbox(
    city_size: tuple = ug.CITY_SIZE,
    district_size: tuple = ug.DISTRICT_SIZE):
    # western border - x_min
    x_min = random.randint(0, city_size[0]-district_size[0])
    # eastern border - x_max
    x_max = x_min + district_size[0]
    # southern border - y_min
    y_min = random.randint(0, city_size[1]-district_size[1])
    # nothern border - y_max
    y_max = y_min + district_size[1]
    district_bbox = [(x_min, y_min),
        (x_max, y_max)]
    return district_bbox

def check_point_within_bbox(
        point: tuple,
        bbox: list,
        ):
    [(x_min, y_min), (x_max, y_max)] = bbox
    if ((x_min <= point[0] <= x_max)
        and (y_min <= point[1] <= y_max)):
        return True
    else:
        return False

def check_segment_within_district(
        segment: dict,
        district_bbox: list,
        ):

    if ((check_point_within_bbox(
        segment['coordinates'][0], district_bbox) is True)
        and (check_point_within_bbox(
        segment['coordinates'][1], district_bbox) is True)):
        return True
    else:
        return False


def get_random_district(
        city: list,
        city_size: tuple = ug.CITY_SIZE,
        district_size: tuple = ug.DISTRICT_SIZE,
        ):
    district_bbox = get_random_district_bbox(city_size, district_size)
    logger.info(f"district borders: {district_bbox}")
    random_district = []
    for segment in city:
        if check_segment_within_district(segment, district_bbox) is True:
            random_district.append(segment)
    return random_district