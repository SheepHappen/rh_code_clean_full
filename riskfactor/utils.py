import math
from decimal import ROUND_HALF_UP, Decimal

import numpy as np


def create_min_max(values_list):
    vals = [value['value'] for value in values_list if value['value'] and (isinstance(value['value'], Decimal) or isinstance(value['value'], int) or isinstance(value['value'], float))]

    if vals:
        v_min = np.percentile(vals, 5)
        v_max = np.percentile(vals, 95)

        return v_min, v_max


def do_skew(val, skew):
    if val <= 0.0:
        return val

    if skew == 'NONE':
        return val

    elif skew == 'POW2':
        return math.pow(val, 2)

    elif skew == 'EX10':
        return math.pow(10, val)

    elif skew == 'LOG':
        return math.log10(val)


def do_transform(value, min_value, max_value):
    try:
        return (99.0 * (float(value) - min_value) / (max_value - min_value)) + 1.
    except:
        return 0.0


def f_positive_1_100(values):
    values_list = [float(value['value']) for value in values if value['value'] and (isinstance(value['value'], Decimal) or isinstance(value['value'], int) or isinstance(value['value'], float))]

    if values_list:
        min_value = min(values_list)
        max_value = max(values_list)

        new_values_list = []
        for value in values:
            if value.get('id'):
                if value.get('id') == 'blank':
                    obj = {
                        'id': value['id'],
                        'name': value['name'],
                        'value': value['value']
                    }
                else:
                    obj = {
                        'id': value['id'],
                        'name': value['name'],
                        'value': do_transform(value['value'], min_value, max_value)
                    }
            else:
                obj = {
                    'risk': value['risk'],
                    'industry': value['industry'],
                    'value': do_transform(value['value'], min_value, max_value),
                }
                if value.get('type'):
                    obj['type'] = value['type']

            new_values_list.append(obj)

        return new_values_list
    else:
        return []


def fmt_4dp(dec_val, map_values=None):
    if map_values and dec_val in map_values:
        return map_values[dec_val]
    else:
        return Decimal(str(dec_val)).quantize(Decimal('1.0000'), ROUND_HALF_UP)
