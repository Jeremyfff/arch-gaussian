import atexit
import json
import logging
import os

from gui import global_info as gi  # global info can be imported here, but global_app_state cannot

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

__runtime__ = True
if not __runtime__:
    raise Exception("This code will never be reached")


class UserData:
    """
    User Data用于记录用户数据，用户不可改动， 但会随着用户使用自动保存
    """

    def __init__(self):
        """
        __init__中填写用户数据的默认值
        """
        self.fullscreen = False
        self.window_size: tuple[int, int] = (1280, 720)  # 窗口大小

        self.layout_level3_left_width: float = 400  # 左边栏分区大小

        self.recent_project_names: list[str] = []  # 最近项目的名称
        self.recent_project_paths: list[str] = []  # 最近项目的路径

        self.can_show_debug_info: bool = False
        self.can_print_key_events: bool = False
        self.can_show_help_info: bool = True

        # scene basic geometry collection
        self.can_show_scene_grid: bool = True
        self.can_show_scene_axis: bool = True
        self.can_show_skybox: bool = True

        self.can_render_geometry: bool = True
        self.can_render_debug_geometry: bool = True
        self.can_render_gaussian: bool = True

        self.renderer_max_frame_rate: int = 60
        self.renderer_point_size: float = 10.0
        self.renderer_downsample: int = 1

        self.program_demands: dict[str: int] = {}  # 每个program需要预加载多少


def load_user_data(_user_data: UserData) -> None:
    """
    从本地文件加载user data。

    本地文件路径定义在global_info.py的USER_DATA_PATH中。

    :param _user_data: 要将内容填入的UserData对象
    :return: 无返回值
    """
    data_path = gi.USER_DATA_PATH
    logger.info(f'loading user data from {os.path.abspath(data_path)}')
    if os.path.exists(data_path):
        with open(data_path, "r") as file:
            json_data: dict = json.load(file)
        for key in _user_data.__dict__.keys():
            if key in json_data:
                setattr(_user_data, key, json_data[key])
                logger.debug(f" {key} found in json, use json value")
            else:
                logger.debug(f" {key} not found in json, use default value")
    else:
        logger.warning(f'user data file not found, use default user data')


def save_user_data(_user_data: UserData) -> None:
    """
    保存User Data

    :param _user_data: 要保存的UserData对象
    :return: 无返回值
    """
    assert _user_data is not None, "User Data is None"
    data_path = gi.USER_DATA_PATH
    logger.info(f'saving user data to {os.path.abspath(data_path)}')
    data = {}
    for key in _user_data.__dict__:
        data[key] = getattr(_user_data, key)
    json_data = json.dumps(data, indent=4)
    with open(data_path, "w") as file:
        file.write(json_data)
    logger.info(f'Successfully write user data to {os.path.abspath(data_path)}')


class UserSettings:
    """
    用户设置，用户可以在运行时修改
    """

    def __init__(self):
        """
        __init__方法中记录用户设置的默认值
        """
        # Note: 此处记录的变量，如果需要在UI界面中显示和修改，需要前往gui.contents.settings_content.py中修改
        # language
        self.language: int = 0  # 默认英语

        self.project_repository_folder = ''
        self.colmap_executable = ''
        self.move_scroll_speed = 0.1
        self.scale_scroll_speed = 0.1
        self.rotate_scroll_speed = 1

        self.grid_fading_distance = 10.0  # 三维格网消隐距离
        self.grid_z_offset = 0.001  # 三维格网z轴偏移距离（防止重叠闪烁）

        # these settings are moved to Style Settings Content
        self.global_scale = 1.0
        self.full_screen_blur_fbt_down_sampling_factor: int = 4  # 全屏模糊降采样系数
        self.full_screen_blur_radius = 32  # 全屏模糊基准像素
        self.bg_style = -1  # -1 为随机

    @property
    def recommended_blur_radius(self):
        return self.full_screen_blur_radius / self.full_screen_blur_fbt_down_sampling_factor


def load_user_settings(_user_settings: UserSettings) -> None:
    """
    从本地文件加载用户设置， 并写入_user_settings对象中。

    本地文件位置定义在global_info.py的USER_SETTINGS_PATH中。

    :param _user_settings: 要写入的UserSettings对象
    :return: 无返回值
    """
    settings_path = gi.USER_SETTINGS_PATH
    logger.info(f'loading user settings from {os.path.abspath(settings_path)}')
    if os.path.exists(settings_path):
        with open(settings_path, "r") as file:
            json_data = json.load(file)
        for key in _user_settings.__dict__:
            if key in json_data:
                setattr(_user_settings, key, json_data[key])
                logger.debug(f" {key} found in json, use json value")
            else:
                logger.debug(f" {key} not found in json, use default value")
    else:
        logger.info(f'user settings file not found, use default user settings')


def save_user_settings(_user_settings: UserSettings) -> None:
    """
    将_user_settings中的用户设置，保存到本地。
    :param _user_settings:
    :return: 无返回值
    """
    assert _user_settings is not None
    settings_path = gi.USER_SETTINGS_PATH
    logger.info(f'saving user settings to {os.path.abspath(settings_path)}')
    data = {}
    for key in _user_settings.__dict__:
        data[key] = getattr(_user_settings, key)

    json_data = json.dumps(data, indent=4)
    with open(settings_path, "w") as file:
        file.write(json_data)
    logger.info(f'Successfully write user data to {os.path.abspath(settings_path)}')


# 在库被导入时执行
user_data = UserData()
user_settings = UserSettings()

load_user_data(user_data)
load_user_settings(user_settings)

atexit.register(lambda: save_user_data(user_data))  # 注册关闭时的动作：保存user data
atexit.register(lambda: save_user_settings(user_settings))  # 注册关闭时的动作：保存user settings
