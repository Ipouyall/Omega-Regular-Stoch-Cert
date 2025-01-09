def _rapid_reversed_dict_replacement(string, **kwargs):
    for key, value in kwargs.items():
        string = string.replace(str(value), str(key))
    return string


def _rapid_dict_replacement(string, **kwargs):
    keep_alive = 1
    while keep_alive != 0:
        keep_alive = 0
        for key, value in kwargs.items():
            _string = string.replace(str(key), str(value))
            keep_alive += 1 if _string != string else 0
            string = _string
    return string


def _fast_dict_replacement(string, lookup: dict, safe=False):
    for key in lookup.keys():
        string = string.replace(str(key), f"'''{key}'''")
    for key, value in lookup.items():
        _v = f"({value})" if safe else str(value)
        string = string.replace(f"'''{key}'''", _v)
    return string
