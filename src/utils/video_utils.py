import cv2
import os
import shutil
from tqdm.auto import tqdm
from src.utils import progress_utils as pu

def extract_frames(video_path: str, target_frames: int, indent_frames:int=0) -> (bool, str):
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
    pu.new_progress(target_frames)

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
            pu.update(1)

        current_frame += 1

    # 释放视频文件句柄
    cap.release()
    print(f"图像保存至{output_folder}")
    return True, output_folder
