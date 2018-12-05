# TEST CASES
random_city = get_random_city(
    west_to_east=2,
    south_to_north=1,
    no_way_frequency=0,
    one_way_forward_frequencey=0,
    one_way_backward_frequencey=0,
    two_way_frequency=1
    )
# OUTPUT
# 0 right turns
# 0 left turns
# 2 u-turns

random_city = get_random_city(
    west_to_east=2,
    south_to_north=2,
    no_way_frequency=0,
    one_way_forward_frequencey=0,
    one_way_backward_frequencey=0,
    two_way_frequency=1
    )
# OUTPUT
# 4 right turns
# 4 left turns
# 8 u-turns

random_city = get_random_city(
    west_to_east=3,
    south_to_north=2,
    no_way_frequency=0,
    one_way_forward_frequencey=0,
    one_way_backward_frequencey=0,
    two_way_frequency=1
    )
# OUTPUT
# 8 right turns
# 8 left turns
# 14 u-turns