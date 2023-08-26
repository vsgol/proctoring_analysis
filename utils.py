import json
import logging
import os

log = logging.getLogger(__name__)


def import_data(folder, keys):
    data = dict()
    if folder is None:
        log.error('Got no path, aborting')
        return data
    if os.path.exists(folder):
        directory = os.listdir(folder)
        directory = list(filter(lambda x: x != 'sum_json.json', directory))
        for json_name in directory:
            with open(folder + '/' + json_name, 'r', encoding='utf-8') as data_file:
                student_data = json.load(data_file)
                name = student_data['student_data'][0].rsplit('/')[-2]
                data[name] = student_data['result'][0] | {'video_len': student_data['video_len']}
                if keys:
                    data[name]['frame_data'] = list(filter(
                        lambda d: ("warn" in d and len([val for val in keys if val in d['warn']]) > 0) or
                                  ("anomalies" in d and len([val for val in keys
                                                             if val in d["anomalies"].keys() and d["anomalies"][val]]))
                        , data[name]['frame_data']))
    else:
        log.error('Got invalid data path: [' + folder + '], aborting.')
    return data


def merge_iterable(iterable, smooth):
    """Merges iterable elements"""

    def merge(prev, nxt):
        return {
            "start_time": prev["start_time"],
            "end_time": max(prev["end_time"], nxt["end_time"])
        }

    iterable = list(iterable)
    if not iterable:
        return []

    merged = []
    while iterable:
        cur_el = iterable.pop(0)
        for el in iterable:
            if cur_el["end_time"] >= el["start_time"]:
                cur_el = merge(cur_el, el)
                iterable.remove(el)
            else:
                break
        merged.append(cur_el)

    if smooth:
        iterable, merged = merged, []
        while iterable:
            cur_el = iterable[0]
            time_stamp = cur_el['start_time'] // smooth * smooth
            time = 0
            for el in iterable:
                time += min(el['end_time'], time_stamp + smooth) - el['start_time']
                cur_el = merge(cur_el, el)
                iterable.remove(el)
                if el['end_time'] >= time_stamp + smooth:
                    el['start_time'] = time_stamp + smooth
                    iterable.insert(0, el)
                    break
            cur_el['end_time'] = time_stamp + smooth
            if time > smooth / 2.0:
                merged.append(cur_el)

    return merged


def join_results(screencast_data, webcam_data, smooth):
    combined = dict()
    for name, data in screencast_data.items():
        combined[name] = {
            'frame_data': sorted(webcam_data[name]['frame_data'] + data['frame_data'], key=lambda p: p['start_time'])}

        for case in combined[name]['frame_data']:
            if case['end_time'] == 0.0:
                case['end_time'] = data['video_len'] if "warn" in case else webcam_data[name]['video_len']
        combined[name]['frame_data'] = merge_iterable(combined[name]['frame_data'], smooth)
    return combined
