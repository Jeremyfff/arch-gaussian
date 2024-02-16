#
# Copyright (C) 2023, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use 
# under the terms of the LICENSE.md file.
#
# For inquiries contact  george.drettakis@inria.fr
#
import subprocess
from errno import EEXIST
from os import makedirs, path
import os
from tqdm.auto import tqdm

def mkdir_p(folder_path):
    # Creates a directory. equivalent to using mkdir -p on the command line
    try:
        makedirs(folder_path)
    except OSError as exc:  # Python >2.5
        if exc.errno == EEXIST and path.isdir(folder_path):
            pass
        else:
            raise


def searchForMaxIteration(folder):
    saved_iters = [int(fname.split("_")[-1]) for fname in os.listdir(folder)]
    return max(saved_iters)


def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

    while True:
        # 逐行读取输出
        output = process.stdout.readline()
        # 输出为空且进程已结束时，退出循环
        if output == '' and process.poll() is not None:
            break
        print(output)

    return process.poll()

def run_colmap_feature_extraction(command):
    # 创建一个tqdm进度条

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

    while True:
        # 逐行读取输出
        output = process.stdout.readline()
        if 'Processed file' in output:
            print(output, end="\r")
            continue
        # 输出为空且进程已结束时，退出循环
        if output == '' and process.poll() is not None:
            break

    return process.poll()

def run_colmap_matching_block(command):
    # 创建一个tqdm进度条

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

    while True:
        # 逐行读取输出
        output = process.stdout.readline()
        if 'Matching block' in output:
            print(output, end="\r")
            continue
        # 输出为空且进程已结束时，退出循环
        if output == '' and process.poll() is not None:
            break

    return process.poll()
def run_colmap_bundle(command, total):
    # # 创建一个tqdm进度条
    # pbar = tqdm(total=total)
    # pbar.n = 0
    # pbar.refresh()

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

    while True:
        # 逐行读取输出
        output = process.stdout.readline()
        if 'Registering' in output:
            # a, b = output.split("(")
            # a, b = b.split(")")
            # pbar.n = int(a)
            # pbar.refresh()
            print(output, end="\r")
            continue
        # 输出为空且进程已结束时，退出循环
        if output == '' and process.poll() is not None:
            break

    # pbar.close()
    return process.poll()



