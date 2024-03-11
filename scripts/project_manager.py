import json
import logging
import os
from typing import Optional

from scripts import global_info


# 所有与项目相关的信息都储存在这里
class Project:

    def __init__(self, project_name, project_root):
        self.project_name = project_name
        self.project_root = project_root
        self.info = {}

    def p_update(self):
        if not self.info:
            self.p_scan()

    def p_restore(self, data: dict):
        """从json data恢复数据"""
        if global_info.VERSION != data['project_version']:
            logging.warning(f'version not match, please take care')
        try:
            self.project_name = data['project_name']
            self.project_root = data['project_root']
            return self
        except Exception as e:
            logging.error(str(e))
            return None

    def p_save(self):
        """保存为json"""
        project_info = {'project_version': global_info.VERSION,
                        'project_name': self.project_name,
                        'project_root': self.project_root}
        # 将字典转换为 JSON 格式
        json_data = json.dumps(project_info, indent=4)  # indent 参数用于格式化输出，使其更易读

        # 将 JSON 数据保存到文件
        tmp_folder = os.path.join(self.project_root, '.arch_gaussian')
        os.makedirs(tmp_folder, exist_ok=True)
        file_path = os.path.join(tmp_folder, 'project.json')
        with open(file_path, "w") as file:
            file.write(json_data)
        logging.info("JSON 数据已保存到文件:", file_path)

    def clear_info(self):
        self.info = {}

    def update_info(self):
        self.clear_info()
        self.p_scan()

    def get_info(self, name):
        return self.info[name]

    def p_scan(self):
        logging.info(f'scanning project info...')
        self.scan_basic()
        self.scan_video()
        self.scan_google_earth_footage()
        self.scan_input_images()
        self.scan_sparse0()
        self.scan_output()

    def scan_basic(self):
        data_root = os.path.join(self.project_root, 'data')
        os.makedirs(data_root, exist_ok=True)
        self.info['data_root'] = data_root

        output_root = os.path.join(self.project_root, 'output')
        os.makedirs(output_root, exist_ok=True)
        self.info['output_root'] = output_root

    def scan_video(self):
        """
        detect video in root/data
        updates:
        mp4_file_names : list[str]
        mp4_file_paths : list[str]
        """
        data_root = self.info['data_root']
        files = os.listdir(data_root)
        mp4_file_names = [file for file in files if file.endswith(".mp4")]
        mp4_file_paths = [os.path.join(data_root, file) for file in mp4_file_names]
        self.info['mp4_file_names'] = mp4_file_names
        self.info['mp4_file_paths'] = mp4_file_paths

    def scan_google_earth_footage(self):
        """
        scan Google Earth footage folder(root/data/footage) and images inside it
        footage_image_folder: str # Google Earth footage folder
        has_footage_image_folder : bool
        footage_image_names : list[str]
        footage_image_paths : list[str]
        """
        data_root = self.info['data_root']
        self.info['footage_image_folder'] = os.path.join(data_root, 'footage')
        files = os.listdir(data_root)
        if 'footage' in files:
            input_path = self.info['footage_image_folder']
            file_names = os.listdir(input_path)
            file_paths = [os.path.join(input_path, file_name) for file_name in file_names]
            self.info['footage_image_names'] = file_names
            self.info['footage_image_paths'] = file_paths
            self.info['has_footage_image_folder'] = True
        else:
            self.info['footage_image_names'] = []
            self.info['footage_image_paths'] = []
            self.info['has_footage_image_folder'] = False

    def scan_input_images(self):
        """
        scan input image folder (root/data/input) and images inside the folder

        updates:
        input_image_folder : str  # input image folder path
        has_input_image_folder : bool  # is input image folder exist
        input_image_names : list[str] # image names in input image folder
        input_image_paths : list[str]  # image paths in input image folder
        """
        data_root = self.info['data_root']
        self.info['input_image_folder'] = os.path.join(data_root, 'input')
        files = os.listdir(data_root)
        if 'input' in files:
            input_path = self.info['input_image_folder']
            file_names = os.listdir(input_path)
            file_paths = [os.path.join(input_path, file_name) for file_name in file_names]
            self.info['input_image_names'] = file_names
            self.info['input_image_paths'] = file_paths
            self.info['has_input_image_folder'] = True
        else:
            self.info['input_image_names'] = []
            self.info['input_image_paths'] = []
            self.info['has_input_image_folder'] = False

    def scan_sparse0(self):
        data_root = self.info['data_root']
        sparse_folder = os.path.join(data_root, 'sparse/0')
        self.info['has_sparse0'] = os.path.exists(sparse_folder)

    def scan_output(self):
        output_root = self.info['output_root']
        output_point_cloud_folder = os.path.join(output_root, 'point_cloud')
        self.info['output_point_cloud_folder'] = output_point_cloud_folder
        has_output_point_cloud_folder = os.path.exists(output_point_cloud_folder)
        self.info['has_output_point_cloud_folder'] = has_output_point_cloud_folder
        if has_output_point_cloud_folder:
            iteration_folder_names = os.listdir(output_point_cloud_folder)
            self.info['output_iteration_folder_names'] = iteration_folder_names
            self.info['output_iteration_folder_paths'] = [os.path.join(output_point_cloud_folder, folder_name)
                                                          for folder_name in iteration_folder_names]
        else:
            self.info['output_iteration_folder_names'] = []
            self.info['output_iteration_folder_paths'] = []




class ProjectManager:
    curr_project: Project = None

    @classmethod
    def get_curr_project_name(cls):
        if cls.curr_project is None:
            return 'no project'
        else:
            return cls.curr_project.project_name

    @classmethod
    def get_curr_project_root(cls):
        if cls.curr_project is None:
            return ''
        else:
            return cls.curr_project.project_root

    @classmethod
    def create_project(cls, project_name, project_root) -> 'Project':
        """创建项目，创建项目文件夹并创建配置文件"""
        if not os.path.isdir(project_root):
            raise Exception(f'project root {project_root} is not a valid folder')
        if not os.path.exists(project_root):
            os.makedirs(project_root)
        project: 'Project' = Project(project_name, project_root)
        os.makedirs(os.path.join(project.project_root, 'data'), exist_ok=True)
        os.makedirs(os.path.join(project.project_root, 'output'), exist_ok=True)
        project.p_scan()
        project.p_save()
        cls.curr_project = project
        return project

    @classmethod
    def open_folder_as_project(cls, folder_path) -> Optional['Project']:
        """打开已有文件夹作为项目， 如果打开项目发生错误，则返回None"""
        if not os.path.isdir(folder_path):
            raise Exception(f'project root {folder_path} is not a valid folder')
        # 首先寻找是否存在配置文件
        project_info_path = os.path.join(folder_path, '.arch_gaussian/project.json')
        if not os.path.exists(project_info_path):
            return None
        # 如果存在配置文件，则读取并用配置文件还原项目信息
        with open(project_info_path, "r") as file:
            json_data = json.load(file)
        # 创建一个空白项目对象
        project = Project(None, None)
        # 校验data目录
        json_changed = False
        if json_data['project_root'] != folder_path:
            logging.warning(f'项目储存的project_root {json_data["project_root"]} 与实际路径不符，正在修正')
            json_data['project_root'] = folder_path
            json_changed = True
        project.p_restore(json_data)
        if json_changed:
            project.p_save()
        project.p_scan()
        cls.curr_project = project
        return project
