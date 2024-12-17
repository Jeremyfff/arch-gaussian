import os
import shutil

import cv2
from PIL import Image
from tqdm.auto import tqdm

from gui.utils import progress_utils as pu


def extract_frames(video_path: str, target_frames: int, indent_frames: int = 0) -> (bool, str):
    # 打开视频文件
    cap = cv2.VideoCapture(video_path)

    # 确保视频文件成功打开
    if not cap.isOpened():
        print("Error: 无法打开视频文件.")
        return False, ""

    output_folder = os.path.join(os.path.dirname(video_path), "input")
    # 确保输出文件夹存在，如果不存在则创建它
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    else:
        print(f"{output_folder}中存在上一批的文件，正在删除...")
        shutil.rmtree(output_folder)
        os.makedirs(output_folder)
    # 获取视频的帧速率和总帧数

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"总帧数: {total_frames}")
    print(f"要抽取的帧数: {target_frames}")
    # 创建一个tqdm对象
    progress_bar = tqdm(total=target_frames)
    pu.p_new_progress("extract_frames", target_frames)

    # 逐帧读取视频并保存为JPG文件
    current_frame = 0
    current_output_frame = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if float(current_frame) / total_frames > float(current_output_frame) / target_frames:
            # 构造输出文件路径
            output_path = os.path.join(output_folder, f"{(current_output_frame + indent_frames + 1):05d}.jpg")

            # 保存帧为JPG文件
            cv2.imwrite(output_path, frame)

            current_output_frame += 1
            progress_bar.update(1)
            pu.p_update("extract_frames", 1)

        current_frame += 1

    # 释放视频文件句柄
    cap.release()
    print(f"图像保存至{output_folder}")
    return True, output_folder


def process_google_earth_frames(input_folder_path, output_folder_path, step, resize):
    if os.path.exists(output_folder_path):
        shutil.rmtree(output_folder_path)
    os.makedirs(output_folder_path)
    # 获取文件夹内的所有文件列表
    file_list = os.listdir(input_folder_path)
    # 按照文件名排序
    sorted_file_list = sorted(file_list)
    sorted_file_list = sorted_file_list[::step]
    # 创建一个tqdm对象
    progress_bar = tqdm(total=len(sorted_file_list))
    pu.p_new_progress("process_google_earth_frames", len(sorted_file_list))
    print(len(sorted_file_list))
    # 重命名文件为序号
    for index, file_name in enumerate(sorted_file_list):

        file_path = os.path.join(input_folder_path, file_name)

        # 打开图像文件
        image = Image.open(file_path)

        # 获取图像的宽度和高度
        width, height = image.size

        # 计算裁剪的区域尺寸
        crop_height = int(height * 0.1)  # 上面 10% 的高度

        # 裁剪图像
        cropped_image = image.crop((0, crop_height, width, height))

        if resize:
            ratio = width / 1920
            resized_image = cropped_image.resize((int(width / ratio), int(height / ratio)))
        else:
            resized_image = cropped_image

        new_file_name = f"{(index + 1):05d}.jpg"  # 根据需要修改文件扩展名
        new_file_path = os.path.join(output_folder_path, new_file_name)
        resized_image.save(new_file_path)

        progress_bar.update(1)
        pu.p_update("process_google_earth_frames", 1)
