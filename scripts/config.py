from argparse import Namespace
import os

project_root = '.'
# scene
scene_name = "your_scene_name"
output_name = ""  # 留空则使用和scene_name一样的配置
# FFMPEG
vid_frames = 200
vid_name = "VID.mp4"

# colmap
colmap_executable = r'C:\Program Files\COLMAP-3.9.1-windows-cuda\COLMAP.bat'
colmap_args = None
_last_colmap_args = None


def update_colmap_args():
    global colmap_args, _last_colmap_args
    _last_colmap_args = colmap_args
    colmap_args = Namespace(
        no_gpu=False,
        skip_matching=False,
        source_path=f"{project_root}/data/{scene_name}",
        camera="OPENCV",
        colmap_executable=colmap_executable,
        resize=False,
        magick_executable=""
    )


update_colmap_args()

# 3dgs training configs
epochs = 3000
resolution = -1
white_background = False
sh_degree = 3
densify_from_iter = 500
densify_until_iter = 15_000
densify_grad_threshold = 0.0002
loaded_iter = None  # None 表示从COLMAP点云创建， 数字表示从之前的训练结果创建
first_iter = None  # None 表示从loaded iter的轮次开始训练，否则则从指定的轮次开始， 该参数影响学习率等参数
args = None
_last_args = None


def update_args():
    global args, _last_args

    _last_args = args

    args = Namespace(
        sh_degree=sh_degree,
        source_path=f"{project_root}/data/{scene_name}",
        model_path=f"{project_root}/output/{output_name if output_name != '' else scene_name}",
        images="images",
        resolution=resolution,
        white_background=white_background,
        data_device="cuda",
        eval=False,

        iterations=epochs,
        position_lr_init=0.00016,
        position_lr_final=0.0000016,
        position_lr_delay_mult=0.01,
        position_lr_max_steps=30_000,
        feature_lr=0.0025,
        opacity_lr=0.05,
        scaling_lr=0.005,
        rotation_lr=0.001,
        percent_dense=0.01,
        lambda_dssim=0.2,
        densification_interval=100,
        opacity_reset_interval=3000,
        densify_from_iter=densify_from_iter,
        densify_until_iter=densify_until_iter,
        densify_grad_threshold=densify_grad_threshold,
        random_background=False,

        convert_SHs_python=False,
        compute_cov3D_python=False,
        debug=False,

        ip="127.0.0.1",
        port=6009,
        debug_from=-1,
        detect_anomaly=False,
        test_iterations=[epochs],
        save_iterations=[epochs],
        quiet=False,
        checkpoint_iterations=[],
        start_checkpoint=None,

        loaded_iter=loaded_iter,
        first_iter=first_iter if first_iter is not None else (loaded_iter if loaded_iter is not None else 0)
    )


update_args()


def find_different_values(obj1, obj2):
    differences = []
    for key, value1 in vars(obj1).items():
        value2 = getattr(obj2, key)
        if value1 != value2:
            differences.append((key, value1, value2))
    return differences


def print_updated_colmap_args():
    # 找到两个Namespace对象的不同之处
    differences = find_different_values(_last_colmap_args, colmap_args)
    for key, value1, value2 in differences:
        print(f'{key}: {value1} => {value2}')


def print_updated_args():
    # 找到两个Namespace对象的不同之处
    differences = find_different_values(_last_args, args)
    for key, value1, value2 in differences:
        print(f'{key}: {value1} => {value2}')
