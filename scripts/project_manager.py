import os
from typing import Optional

from scripts import global_info
import json


# 所有与项目相关的信息都储存在这里
class Project:
    def __init__(self, project_name, project_root):
        self.project_name = project_name
        self.project_root = project_root

    @staticmethod
    def create_project(project_name, project_root) -> 'Project':
        """创建项目，创建项目文件夹并创建配置文件"""
        if not os.path.isdir(project_root):
            raise Exception(f'project root {project_root} is not a valid folder')
        if not os.path.exists(project_root):
            os.makedirs(project_root)
        project = Project(project_name, project_root)
        os.makedirs(os.path.join(project.project_root, 'data'), exist_ok=True)
        os.makedirs(os.path.join(project.project_root, 'output'), exist_ok=True)
        project.save()
        return project

    @staticmethod
    def open_folder_as_project(folder_path) -> Optional['Project']:
        """打开已有文件夹作为项目， 如果打开项目发生错误，则返回None"""
        if not os.path.isdir(folder_path):
            raise Exception(f'project root {folder_path} is not a valid folder')
        # 首先寻找是否存在配置文件
        project_info_path = os.path.join(folder_path, '.arch_gaussian/project.json')
        if os.path.exists(project_info_path):
            # 如果存在配置文件，则读取并用配置文件还原项目信息
            with open(project_info_path, "r") as file:
                json_data = json.load(file)
            project = Project(None, None)
            # 校验data目录
            json_changed = False
            if json_data['project_root'] != folder_path:
                print(f'项目储存的project_root {json_data["project_root"]} 与实际路径不符，正在修正')
                json_data['project_root'] = folder_path
                json_changed = True
            project.restore(json_data)
            if json_changed:
                project.save()
            return project
        else:
            return None
            # 如果没有配置文件，则在文件夹下创建新的项目
            # project = Project.create_project(os.path.basename(folder_path), folder_path)
            # return project

    def restore(self, data: dict):
        if global_info.VERSION != data['project_version']:
            print(f'version not match, please take care')
        try:
            self.project_name = data['project_name']
            self.project_root = data['project_root']
            return self
        except Exception as e:
            print(str(e))
            return None


    def save(self):
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
        print("JSON 数据已保存到文件:", file_path)


curr_project: Optional[Project] = None
