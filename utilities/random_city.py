import random
import matplotlib.pyplot as plt

import shapely as sh
from shapely import geometry

WEST_TO_EAST = 12
SOUTH_TO_NORTH = 8

NO_WAY_FREQUENCY = 0.2
TWO_WAY_FREQUENCY = 0.5
ONE_WAY_FORWARD_FREQUENCY = 0.15
ONE_WAY_BACKWARD_FREQUENCY = 0.15

random.seed(0)


# VISUALISE RANDOM CITY ========================================================
def plot_city(
        city: list):
    
    plt.figure(figsize=(12, 8))
    for segment in city:
        x, y = zip(*segment['coordinates'])
        plt.plot(x, y)
    plt.axis('off')
    plt.show

def get_city_statistics(
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
        no_way_frequency: float = NO_WAY_FREQUENCY,
        one_way_forward_frequencey: float = ONE_WAY_FORWARD_FREQUENCY,
        one_way_backward_frequencey: float = ONE_WAY_BACKWARD_FREQUENCY,
        two_way_frequency: float = TWO_WAY_FREQUENCY):
    direction = random.choices(
        [0, 1, 2, 3],
        weights=[
            no_way_frequency,
            one_way_forward_frequencey,
            one_way_backward_frequencey,
            two_way_frequency],
        k=1)[0]
    return direction

def get_street_segments(
        segment_id: int,
        coordinates: list,
        west_to_east: int = WEST_TO_EAST,
        south_to_north: int = SOUTH_TO_NORTH,
        no_way_frequency: float = NO_WAY_FREQUENCY,
        one_way_forward_frequencey: float = ONE_WAY_FORWARD_FREQUENCY,
        one_way_backward_frequencey: float = ONE_WAY_BACKWARD_FREQUENCY,
        two_way_frequency: float = TWO_WAY_FREQUENCY
        ):
    direction = get_random_direction(
        no_way_frequency,
        one_way_forward_frequencey,
        one_way_backward_frequencey,
        two_way_frequency)
    if ((direction == 0)
        or (coordinates[1][0] >= west_to_east)
        or (coordinates[1][1] >= south_to_north)):
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
        west_to_east: int = WEST_TO_EAST,
        south_to_north: int = SOUTH_TO_NORTH,
        no_way_frequency: float = NO_WAY_FREQUENCY,
        one_way_forward_frequencey: float = ONE_WAY_FORWARD_FREQUENCY,
        one_way_backward_frequencey: float = ONE_WAY_BACKWARD_FREQUENCY,
        two_way_frequency: float = TWO_WAY_FREQUENCY
        ) -> list:
    city = []
    segment_id = 1
    for i in range(west_to_east):
        for j in range(south_to_north):
            segments = get_street_segments(
                segment_id,
                [(i, j), (i+1, j)],
                west_to_east,
                south_to_north,
                no_way_frequency,
                one_way_forward_frequencey,
                one_way_backward_frequencey,
                two_way_frequency)
            for s in segments:
                city.append(s)
            segment_id += 1

            segments = get_street_segments(
                segment_id,
                [(i, j), (i, j+1)],
                west_to_east,
                south_to_north,
                no_way_frequency,
                one_way_forward_frequencey,
                one_way_backward_frequencey,
                two_way_frequency)
            for s in segments:
                city.append(s)
            segment_id += 1

    return city