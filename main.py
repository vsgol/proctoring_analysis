import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as md
import datetime as dt

from utils import import_data, join_results


def build_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("screencast_path", type=str, help="path to screencast data")
    parser.add_argument("webcam_path", type=str, help="path to webcam data")
    parser.add_argument("validation_path", type=str, help="path to validation data")
    parser.add_argument("-f", "--flags", type=str, help="flags of proctoring with violations", default='')
    parser.add_argument("-t", "--tag", type=str, help="tag with the type of task with cheating", default='')
    parser.add_argument("--smooth", type=int, help="the minimum violation must be x/2 seconds", default=0)

    return parser


def get_proctoring_flags(keys_string):
    keys_string = keys_string.upper()
    keys = []
    if 'M' in keys_string:
        keys.append('messenger')
    if 'B' in keys_string:
        keys.append('browser')
    if 'U' in keys_string:
        keys.append('unknown_persons')
    if 'D' in keys_string:
        keys.append('student_not_detected')
    if 'W' in keys_string:
        keys.append('student_not_looking_on_monitor')
    return keys


def get_task_tags(tags_string):
    tags_string = tags_string.upper()
    tags = []
    if 'M' in tags_string:
        tags.append('messenger')
    if 'B' in tags_string:
        tags.append('browser')
    if 'U' in tags_string:
        tags.append('unknown_persons')
    if 'P' in tags_string:
        tags.append('phone_usage')
    if 'F' in tags_string:
        tags.append('foreign_sounds')
    if 'S' in tags_string:
        tags.append('additional_monitor')
    if 'H' in tags_string:
        tags.append('trying_to_hide')
    return tags


def make_df(data):
    df = pd.DataFrame.from_records(data['frame_data'])
    df['start_time'] = md.date2num([dt.datetime.fromtimestamp(ts) for ts in df['start_time']])
    df['end_time'] = md.date2num([dt.datetime.fromtimestamp(ts) for ts in df['end_time']])
    df['duration'] = (df['end_time'] - df['start_time'])
    return df


def main(args):
    proctoring_keys = get_proctoring_flags(args.flags)
    val_keys = get_task_tags(args.tag)

    screencast_data = import_data(args.screencast_path, proctoring_keys)
    webcam_data = import_data(args.webcam_path, proctoring_keys)
    validation_data = import_data(args.validation_path, val_keys)

    prediction_data = join_results(screencast_data, webcam_data, args.smooth)

    for student, v_s in validation_data.items():
        p_s = prediction_data[student]
        v_df = make_df(v_s)
        p_df = make_df(p_s)

        plt.figure(figsize=(16, 8))
        plt.barh(y=student + ' real', width=v_df['duration'], left=v_df['start_time'])
        plt.barh(y=student + ' proctor', width=p_df['duration'], left=p_df['start_time'])
        ax = plt.gca()
        ax.xaxis.grid()
        start, end = ax.get_xlim()
        ax.xaxis.set_ticks(np.linspace(start, end, 25))
        xfmt = md.DateFormatter('%M:%S')
        ax.xaxis.set_major_formatter(xfmt)
        plt.show()


if __name__ == "__main__":
    args = build_argparser().parse_args()
    main(args)
