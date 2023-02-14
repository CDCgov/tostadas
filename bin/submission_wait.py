#!/usr/bin/env python3

import time 
import argparse


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait_time", type=str, help='Length of time to wait in seconds')
    return parser


def main():
    args = get_args().parse_args()
    parameters = vars(args)
    time_2_wait = int(parameters['wait_time'])
    time.sleep(time_2_wait)


if __name__ == "__main__":
    main()