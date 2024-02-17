
from flask import Flask, request
import os
import json

from utils.graphics_utils import tr2pa
from scipy.spatial.transform import Rotation as R
import numpy as np

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"


@app.route("/get_basic_info")
def get_basic_info():
    return "Hello, World!"

@app.route("/set_cam_pos")
def set_cam_pos():
    return {'pos', }

@app.route("/get_cam_pos")
def get_cam_pos():
    try:
        index = int(request.args['index'])
        assert len(camera_info_list) > 0, "camera info list is empty"
        if index >= len(camera_info_list):
            index = len(camera_info_list) - 1
        if index < 0:
            index = 0
        cam = camera_info_list[index]
        print(cam.keys())
        # pos, axis = tr2pa(np.array(cam['position']), np.array(cam['rotation']))
        pos = np.array(cam['position']).tolist()
        pos[2] *= -1
        rotation = np.array(cam['rotation'])
        # _, axis = tr2pa(np.array(cam['position']), np.array(cam['rotation']))
        # axis = axis.transpose()
        # axis[:,2] *= -1
        #axis[1] *= -1
        #axis[0] *= -1

        euler = R.from_matrix(rotation).as_euler('XYZ', degrees=True).astype(np.float32).tolist()

        return {'status':'success', 'pos':{'x':pos[0], 'y':pos[1], 'z':pos[2]}, 'euler':{'x':euler[0], 'y':euler[1], 'z':euler[2]}}
    except Exception as e:
        print(str(e))
        return {'status':'error', 'message': str(e)}



try:
    import config

    config.scene_name = "TestCity6"
    config.epochs = 15000
    config.update_args()
    config.update_colmap_args()

    print(config.args)
    # 打开JSON文件
    with open(os.path.join(config.args.model_path, "cameras.json")) as f:
        # 使用json.load()方法加载JSON数据
        camera_info_list = json.load(f)

except Exception as e:
    print(str(e))
    exit(1)


if __name__ == "__main__":

    app.run(host='0.0.0.0', port=8999)