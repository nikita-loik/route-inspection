# TEST CASES
random_city = get_random_city(
    city_size = [2, 1],
    frequencies = [0, 0, 0, 1],
    )
# OUTPUT
# 0 right turns
# 0 left turns
# 2 u-turns

random_city = get_random_city(
    city_size = [2, 2],
    frequencies = [0, 0, 0, 1],
    )
# OUTPUT
# 4 right turns
# 4 left turns
# 8 u-turns

random_city = get_random_city(
    city_size = [3, 2],
    frequencies = [0, 0, 0, 1],
    )
# OUTPUT
# 8 right turns
# 8 left turns
# 14 u-turns

# Test for rejoining the split edges.
random_city = get_random_city(
    city_size = [3, 1],
    frequencies = [0, 0, 0, 1],
    )
# OUTPUT
# 8 right turns
# 8 left turns
# 14 u-turns