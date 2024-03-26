import atexit
import json
import logging
import os

# user data 是一些记录用户信息的数据，用户无法编辑
default_user_data = {
    'last_nav_idx': -1,
    'layout_level3_left_width': 400,
}
user_data = {}

# user settings是记录用户设置和偏好的数据，用户可以编辑
default_user_settings = {
    'project_repository_folder': '',
    'colmap_executable': ''
}

user_settings = {}


def _load_user_data_items(json_data):
    """批量从json 数据中加载到 user_data"""
    for key in default_user_data:
        if key in json_data:
            user_data[key] = json_data[key]
        else:
            print(f'{key} not found in json data, use default value')
            user_data[key] = default_user_data[key]


def _load_user_settings_items(json_data):
    """批量从json 数据中加载到 user_data"""
    for key in default_user_settings:
        if key in json_data:
            user_settings[key] = json_data[key]
        else:
            print(f'{key} in user settings not found in json data, use default value')
            user_settings[key] = default_user_settings[key]

def load_user_data():
    global user_data
    user_data_path = '.userdata'
    print(f'loading user data from {os.path.abspath(user_data_path)}')
    if os.path.exists(user_data_path):
        # 如果存在配置文件，则读取并用配置文件还原项目信息
        with open(user_data_path, "r") as file:
            json_data = json.load(file)
        _load_user_data_items(json_data)

    else:
        print(f'user data file not found, use default user data')
        user_data = default_user_data.copy()
    print(user_data)

def load_user_settings():
    global user_settings
    user_settings_path = '.usersettings'
    print(f'loading user settings from {os.path.abspath(user_settings_path)}')
    if os.path.exists(user_settings_path):
        # 如果存在配置文件，则读取并用配置文件还原项目信息
        with open(user_settings_path, "r") as file:
            json_data = json.load(file)
        _load_user_settings_items(json_data)
    else:
        print(f'user settings file not found, use default user settings')

        user_settings = default_user_settings.copy()
    print(user_settings)
def save_user_data():
    assert user_data != {}
    user_data_path = '.userdata'
    print(f'saving user data to {os.path.abspath(user_data_path)}')
    json_data = json.dumps(user_data, indent=4)
    with open(user_data_path, "w") as file:
        file.write(json_data)


def save_user_settings():
    assert user_settings != {}
    user_settings_path = '.usersettings'
    print(f'saving user settings to {os.path.abspath(user_settings_path)}')
    json_data = json.dumps(user_settings, indent=4)
    with open(user_settings_path, "w") as file:
        file.write(json_data)


def clear_user_data():
    global user_data
    print(f'user data reset to default')
    user_data = default_user_data


def clear_user_settings():
    global user_settings
    print(f'user settings reset to default')
    user_settings = default_user_settings


load_user_data()
load_user_settings()
atexit.register(save_user_data)  # 注册关闭时的动作： 保存user data
atexit.register(save_user_settings)  # 注册关闭时动作： 保存user settings
