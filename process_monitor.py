#!/usr/bin/env python
# Copyright (c) 2015-2016 University Corporation for Atmospheric Research/Unidata
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT

from datetime import datetime

import boto3
import psutil


def find_proc(proc_name):
    for proc in psutil.process_iter():
        try:
            cmd = proc.cmdline()
            if len(cmd) >= 2 and cmd[0] == 'python' and proc_name in cmd[1]:
                return proc
        except psutil.AccessDenied:
            pass


def make_data(name, value):
    return {'MetricName': name, 'Timestamp': datetime.utcnow(), 'Value': value,
            'Unit': 'Percent'}


def dump_stats(client, proc):
    client.put_metric_data(Namespace='ProcessMetrics',
                           MetricData=[make_data('CPUUsage', proc.cpu_percent(1.0)),
                                       make_data('MemoryUsage', proc.memory_percent())])


if __name__ == '__main__':
    import argparse
    import sys
    import time

    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Monitor Python script stats.')
    parser.add_argument('-i', '--interval', help='Monitoring interval in seconds', type=int,
                        default=10)
    parser.add_argument('name', help='Name of script to monitor', type=str)
    args = parser.parse_args()

    proc_name = sys.argv[1]

    client = boto3.client('cloudwatch')
    while True:
        try:
            proc = find_proc(args.name)
            if not proc:
                time.sleep(args.interval)
            else:
                while True:
                    dump_stats(client, proc)
                    time.sleep(args.interval)
        except psutil.NoSuchProcess:
            pass
