def calculate_skew(exposure, v_min, v_max, origional_data_order, data_order):
    value = 10.0 * (float(exposure) - v_min) / (v_max - v_min)

    # tie back to boundary
    value = min(10.0, value)
    value = max(0.0, value)

    if origional_data_order == 'ASC' and data_order == 'DESC' or origional_data_order == 'DESC' and data_order == 'ASC':
        value = 10.0 - value

    return value


def get_rating(exposure):
    if exposure is None or isinstance(exposure, str):
        return 'No data'
    if exposure <= 1:
        return 'Very Low'
    elif exposure <= 2:
        return 'Low'
    elif exposure <= 4:
        return 'Medium'
    elif exposure <= 6:
        return 'Medium to high'
    elif exposure <= 8:
        return 'High'
    elif exposure > 8:
        return 'Very High'
