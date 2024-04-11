from argparse import Namespace
from enum import Enum

from scripts.project_manager import ProjectManager


class ArgType(Enum):
    NONE = -1
    INTEGER = 0
    FLOAT = 1
    STRING = 2
    PATH = 3
    BOOLEAN = 4
    DICT = 5
    FLOAT2 = 6
    INT2 = 7
    FOLDER = 8
    OPTIONAL_INT = 9


args_dict = {
    'epochs': 3000,
    'resolution': -1,
    'white_background': False,
    'densify_from_iter': 500,
    'densify_until_iter': 15_000,
    'densify_grad_threshold': 0.0002,
    'loaded_iter': None,  # None 表示从COLMAP点云创建， 数字表示从之前的训练结果创建
    'first_iter': None,  # None 表示从loaded iter的轮次开始训练，否则则从指定的轮次开始， 该参数影响学习率等参数
}
args_type_dict = {
    'epochs': ArgType.INTEGER,
    'resolution': ArgType.INTEGER,
    'white_background': ArgType.BOOLEAN,
    'densify_from_iter': ArgType.INTEGER,
    'densify_until_iter': ArgType.INTEGER,
    'densify_grad_threshold': ArgType.FLOAT,
    'loaded_iter': ArgType.OPTIONAL_INT,  # None 表示从COLMAP点云创建， 数字表示从之前的训练结果创建
    'first_iter': ArgType.OPTIONAL_INT,  # None 表示从loaded iter的轮次开始训练，否则则从指定的轮次开始， 该参数影响学习率等参数
}


def gen_config_args():
    args = Namespace(
        sh_degree=3,
        source_path=ProjectManager.curr_project.get_info('data_root'),
        model_path=ProjectManager.curr_project.get_info('output_root'),
        images="images",
        resolution=args_dict['resolution'],
        white_background=args_dict['white_background'],
        data_device="cuda",
        eval=False,

        iterations=args_dict['epochs'],
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
        densify_from_iter=args_dict['densify_from_iter'],
        densify_until_iter=args_dict['densify_until_iter'],
        densify_grad_threshold=args_dict['densify_grad_threshold'],
        random_background=False,

        convert_SHs_python=False,
        compute_cov3D_python=False,
        debug=False,

        ip="127.0.0.1",
        port=6009,
        debug_from=-1,
        detect_anomaly=False,
        test_iterations=[args_dict['epochs']],
        save_iterations=[args_dict['epochs']],
        quiet=False,
        checkpoint_iterations=[],
        start_checkpoint=None,

        loaded_iter=args_dict['loaded_iter'],
        first_iter=args_dict['first_iter'] if args_dict['first_iter'] is not None else (
            args_dict['loaded_iter'] if args_dict['loaded_iter'] is not None else 0)
    )
    return args
