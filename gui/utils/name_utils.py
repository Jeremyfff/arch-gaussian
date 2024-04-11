import os


def get_next_name_idx(names_list):
    max_num = -1
    for name in names_list:
        num_str = ""
        for char in reversed(name):
            if char.isdigit():
                num_str = char + num_str
            else:
                break
        if num_str:
            last_num = int(num_str)
            if last_num > max_num:
                max_num = last_num
    return max_num + 1


def ply_path_to_model_name(ply_path):
    if ply_path is None or ply_path == '':
        return ''
    # 根据路径分隔符进行拆分
    ply_path = os.path.abspath(ply_path)
    ply_path = os.path.normpath(ply_path)
    ply_path = ply_path.replace('.ply', '')
    path_segments = ply_path.split(os.path.sep)

    # 从后往前遍历路径分段
    for i, segment in enumerate(reversed(path_segments)):
        if segment.startswith("point_cloud"):
            continue
        if segment.startswith("iteration"):
            continue
        if segment == 'output':
            continue
        return segment
    return ''
