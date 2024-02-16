import json
import os
import sys

import config

sys.path.append('./src')
import time

import torch
import torch.nn.functional as F
from scene import Scene, GaussianModel
from scene.cameras import MiniCam
from gaussian_renderer import render
from utils.arg_utils import parse_args
import numpy as np
import dearpygui.dearpygui as dpg

config.scene_name = 'TestCity5'
config.epochs = 15000
config.update_args()
config.update_colmap_args()
from config import args, epochs


class GUI:

    def __init__(self, show_gui=True, scale=0.5):
        self.show_gui = show_gui
        self.scale = scale

        # scene
        self.scene_info = None
        self.dataset = None
        self.opt = None
        self.pipe = None
        self.background = None
        self.gaussians = None

        # camera
        self.H = None
        self.W = None
        self.mini_cam: MiniCam = None

        # gui
        self.buffer_image = None

        # utils
        self.need_update = True
        self._last_frame_time = 0
        self.delta_time = 0

        # main loop start
        # ==================start=================
        self.start()
        self._last_frame_time = time.time()
        # main loop
        while dpg.is_dearpygui_running():
            print("start of main loop", end="  ")
            # before update
            self.delta_time = time.time() - self._last_frame_time
            self.delta_time = 0.01 if self.delta_time < 0.01 else self.delta_time

            # =================update =======================
            print("before update", end="  ")
            self.update()

            # after update
            print("after update", end="  ")
            dpg.render_dearpygui_frame()

            self._last_frame_time = time.time()
            print("end of main loop", end="\r")

    def start(self):
        # start will always be executed
        self.load_scene()
        if self.show_gui:
            self.register_dgp()

    def update(self):
        # update func will be run each frame
        # note that update will not run when no gui
        self.mini_cam.update()
        self.render_to_gui()

    def register_dgp(self):
        assert self.mini_cam is not None, "mini_cam not loaded"
        self.W = int(self.mini_cam.image_width * self.scale)
        self.H = int(self.mini_cam.image_height * self.scale)
        dpg.create_context()
        with dpg.texture_registry(show=False):
            dpg.add_raw_texture(
                self.W,
                self.H,
                np.ones((self.W, self.H, 3), dtype=np.float32),
                format=dpg.mvFormat_Float_rgb,
                tag="_texture",
            )
        # the rendered image, as the primary window
        with dpg.window(
                tag="_primary_window",
                width=self.W,
                height=self.H,
                pos=[0, 0],
                no_move=True,
                no_title_bar=True,
                no_scrollbar=True,
        ):
            # add the texture
            dpg.add_image("_texture")

        # dpg.set_primary_window("_primary_window", True)

        # control window
        with dpg.window(
                label="Control",
                tag="_control_window",
                width=400,
                height=self.H,
                pos=[self.W, 0],
                no_move=True,
                no_title_bar=True,
        ):
            # timer stuff
            with dpg.group(horizontal=True):
                dpg.add_text("Infer time: ")
                dpg.add_text("no data", tag="_log_infer_time")
            # camera
            with dpg.group(horizontal=True):
                pass

        ### register camera handler

        def callback_camera_drag_rotate_or_draw_mask(sender, app_data):
            if not dpg.is_item_focused("_primary_window"):
                return
            dx = app_data[1]
            dy = app_data[2]
            print(dx, dy)
            self.mini_cam.move_locally(np.array([dx / 1000, 0, dy / 1000]))
            # self.orbit_cam.orbit(dx, dy)

        def callback_camera_wheel_scale(sender, app_data):
            if not dpg.is_item_focused("_primary_window"):
                return
            delta = app_data
            # self.orbit_cam.scale(delta)

        def callback_camera_drag_pan(sender, app_data):
            if not dpg.is_item_focused("_primary_window"):
                return
            dx = app_data[1]
            dy = app_data[2]
            # self.orbit_cam.pan(dx, dy)

        # def key_press_handler(sender, app_data):
        #     if app_data == ord('W') or app_data == ord('w'):
        #         print("w")
        #         # self.mini_cam.move_locally(np.array([0,0,1 * self.delta_time]))
        #     elif app_data == ord('A') or app_data == ord('a'):
        #         print("a")
        #         # self.mini_cam.move_locally(np.array([1 * self.delta_time,0,0]))
        #     elif app_data == ord('S') or app_data == ord('s'):
        #         print("s")
        #         # self.mini_cam.move_locally(np.array([0,0,-1 * self.delta_time]))
        #     elif app_data == ord('D') or app_data == ord('d'):
        #         print("d")
        #         # self.mini_cam.move_locally(np.array([-1 * self.delta_time,0,0]))

        with dpg.handler_registry():
            # for camera moving
            dpg.add_mouse_drag_handler(
                button=dpg.mvMouseButton_Left,
                callback=callback_camera_drag_rotate_or_draw_mask,
            )
            dpg.add_mouse_wheel_handler(callback=callback_camera_wheel_scale)
            dpg.add_mouse_drag_handler(
                button=dpg.mvMouseButton_Middle, callback=callback_camera_drag_pan
            )
            # dpg.add_key_press_handler(callback=key_press_handler)

        dpg.create_viewport(
            title="Arch Gaussian",
            width=self.W + 400,
            height=self.H + (45 if os.name == "nt" else 0),
            resizable=False,
        )

        dpg.setup_dearpygui()
        dpg.show_viewport()
        self._last_frame_time = time.time()

    def load_scene(self):
        self.dataset, self.opt, self.pipe = parse_args(args)
        ply_path = os.path.join(self.dataset.model_path,
                                "point_cloud",
                                "iteration_" + str(epochs),
                                "point_cloud.ply")
        print(f"loading gaussian model from ply file from {ply_path}")
        self.gaussians = GaussianModel(self.dataset.sh_degree)
        self.gaussians.load_ply(ply_path)
        self.gaussians._xyz.detach()
        self.gaussians._features_dc.detach()
        self.gaussians._features_rest.detach()
        self.gaussians._scaling.detach()
        self.gaussians._rotation.detach()
        self.gaussians._opacity.detach()
        self.gaussians.max_radii2D.detach()
        self.gaussians.xyz_gradient_accum.detach()
        self.gaussians.denom.detach()
        # with torch.no_grad():
        #     # 定义坐标范围
        #     min_coord = torch.tensor([0.0, 0.0, 0.0]).cuda()
        #     max_coord = torch.tensor([1, 1, 100]).cuda()
        #
        #     mask = (self.gaussians.get_xyz >= min_coord) & (self.gaussians.get_xyz <= max_coord)
        #     selected_indices = torch.all(mask, dim=1)
        #     self.gaussians._features_dc[selected_indices] = torch.tensor([-2.0,-2.0, -2.0]).cuda()
        #     print(self.gaussians._features_rest.shape)
        #     self.gaussians._features_rest[selected_indices] = torch.zeros([15,3]).cuda()

        bg_color = [1, 1, 1] if self.dataset.white_background else [0, 0, 0]
        self.background = torch.tensor(bg_color, dtype=torch.float32, device="cuda")

        # creating cam
        print("creating cam")
        with open(os.path.join(args.model_path, "cameras.json")) as f:
            # 使用json.load()方法加载JSON数据
            camera_info_list = json.load(f)

        cam = camera_info_list[0]
        self.mini_cam = MiniCam(np.array(cam['position']), np.array(cam['rotation']), cam['width'], cam['height'],
                                cam['fx'],
                                cam['fy'])

        self.mini_cam.set_transform(np.array([1, 5, -1]), np.array([110, -10, 20]))

    def render_to_gui(self):
        with torch.no_grad():
            starter = torch.cuda.Event(enable_timing=True)
            ender = torch.cuda.Event(enable_timing=True)
            starter.record()

            render_pkg = render(self.mini_cam, self.gaussians, self.pipe, self.background)
            buffer_image = render_pkg["render"]

            buffer_image = F.interpolate(
                buffer_image.unsqueeze(0),
                size=(self.H, self.W),
                mode="bilinear",
                align_corners=False,
            ).squeeze(0)

            self.buffer_image = (
                buffer_image.permute(1, 2, 0)
                .contiguous()
                .clamp(0, 1)
                .contiguous()
                .detach()
                .cpu()
                .numpy()
            )

            ender.record()
            torch.cuda.synchronize()
            t = starter.elapsed_time(ender)

            dpg.set_value("_log_infer_time", f"{t:.4f}ms ({int(1000 / t)} FPS)")
            dpg.set_value(
                "_texture", self.buffer_image
            )  # buffer must be contiguous, else seg fault!


if __name__ == "__main__":
    gui = GUI(show_gui=True)
