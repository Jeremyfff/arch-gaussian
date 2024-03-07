import copy
import json
import math
import os
import random
import uuid
from argparse import Namespace
from enum import Enum
from scripts import config
from gaussian_renderer import render

from scene import GaussianModel
from utils.arg_utils import parse_args
from utils.camera_utils import camera_to_JSON, cameraList_from_camInfos
from utils.image_utils import get_pil_image, save_pil_image
import torch
from tqdm.auto import tqdm
from utils.loss_utils import l1_loss, ssim
from manager.camera_manager import CameraManager
from manager.gaussian_manager import GaussianManager

try:
    from torch.utils.tensorboard import SummaryWriter

    TENSORBOARD_FOUND = True
except ImportError:
    TENSORBOARD_FOUND = False


class SnapshotCameraMode(Enum):
    RAW = 0
    STILL = 1
    ROTATE = 2
    SLOW_ROTATE = 3


class SnapshotFilenameMode(Enum):
    BY_ITERATION = 0
    BY_SNAP_COUNT = 1


snap_count = 0


def init_snapshot(start_count=0):
    global snap_count
    snap_count = start_count


def take_snapshot(_cm: CameraManager, _gm: GaussianManager, _camera_mode=SnapshotCameraMode.RAW, _slow_ratio=5,
                  _filename_mode=SnapshotFilenameMode.BY_ITERATION,
                  _folder_name="snapshots", _iteration_gap=100, _first_period_iteration_gap=10, _first_period_end=100,
                  **kwargs):
    """
    @Jeremy
    自动拍照功能

    """
    _args = kwargs['args']
    _iteration = kwargs['iteration']
    _image = kwargs['image']

    global snap_count
    if (_iteration < _first_period_end and _iteration % _first_period_iteration_gap == 0) or (_iteration % _iteration_gap == 0):
        if _camera_mode == SnapshotCameraMode.RAW:
            _camera = None
        elif _camera_mode == SnapshotCameraMode.STILL:
            _camera = _cm.pick_camera(0)
        elif _camera_mode == SnapshotCameraMode.ROTATE:
            _camera = _cm.pick_camera(snap_count % len(_cm.train_cameras[1.0]))
        elif _camera_mode == SnapshotCameraMode.SLOW_ROTATE:
            _num_cameras = len(_cm.train_cameras[1.0])
            _f = (snap_count / (_num_cameras * _slow_ratio)) % 1.0
            # print(f"_f = {_f}")
            _f_idx = _f * _num_cameras
            _camera1_idx = math.floor(_f_idx) % _num_cameras
            _camera2_idx = (_camera1_idx + 1) % _num_cameras
            # if _camera2_idx < _camera1_idx:
            #     _camera1_idx = _camera2_idx
            #     _camera2_idx += 1
            #     _f_idx = (_f_idx + 1) % _num_cameras
            # _percent1 = abs(_camera2_idx - _f_idx) % 1
            _percent2 = abs(_f_idx - _camera1_idx) % 1
            _percent1 = 1 - _percent2
            _camera1 = _cm.pick_camera(_camera1_idx)
            _camera2 = _cm.pick_camera(_camera2_idx)
            _camera = copy.deepcopy(_camera1)
            _camera.T = _camera1.T * _percent1 + _camera2.T * _percent2
            _camera.R = _camera1.R * _percent1 + _camera2.R * _percent2

            _camera.update()
        else:
            _camera = None
            raise Exception(f"Unexpected camera mode {_camera_mode}")

        if _camera_mode == SnapshotCameraMode.RAW:
            pil_image = get_pil_image(_image)
        else:
            pil_image = _gm.render(_camera, convert_to_pil=True)

        snap_count += 1

        if _filename_mode == SnapshotFilenameMode.BY_ITERATION:
            _save_path = os.path.join(_args.model_path, _folder_name, f"{_iteration:05d}.jpg")
        elif _filename_mode == SnapshotFilenameMode.BY_SNAP_COUNT:
            _save_path = os.path.join(_args.model_path, _folder_name, f"{snap_count:05d}.jpg")
        else:
            _save_path = None
            raise Exception(f"Unexpected filename mode {_filename_mode}")
        save_pil_image(pil_image, _save_path)

        # pil_gt_iamge = get_pil_image(gt_image)
        # gt_save_path = os.path.join(args.model_path, "snap_shots", f"{iteration:05d}_gt.jpg")
        # save_pil_image(pil_gt_iamge, gt_save_path)


def prepare_output_and_logger(args):
    if not args.model_path:
        if os.getenv('OAR_JOB_ID'):
            unique_str = os.getenv('OAR_JOB_ID')
        else:
            unique_str = str(uuid.uuid4())
        args.model_path = os.path.join("./output/", unique_str[0:10])

    # Set up output folder
    print("Output folder: {}".format(args.model_path))
    os.makedirs(args.model_path, exist_ok=True)
    with open(os.path.join(args.model_path, "cfg_args"), 'w') as cfg_log_f:
        cfg_log_f.write(str(Namespace(**vars(args))))

    # Create Tensorboard writer
    tb_writer = None
    if TENSORBOARD_FOUND:
        tb_writer = SummaryWriter(args.model_path)
    else:
        print("Tensorboard not available: not logging progress")
    return tb_writer


def init_output_folder(args, scene_info):
    if not args.loaded_iter:

        print("init output folder...")
        if not os.path.exists(args.model_path):
            print(f"creating folder {args.model_path}")
            os.makedirs(args.model_path, exist_ok=True)
        with open(scene_info.ply_path, 'rb') as src_file, open(os.path.join(args.model_path, "input.ply"),
                                                               'wb') as dest_file:
            dest_file.write(src_file.read())
        json_cams = []
        camlist = []
        if scene_info.test_cameras:
            camlist.extend(scene_info.test_cameras)
        if scene_info.train_cameras:
            camlist.extend(scene_info.train_cameras)
        for id, cam in enumerate(camlist):
            json_cams.append(camera_to_JSON(id, cam))
        with open(os.path.join(args.model_path, "cameras.json"), 'w') as file:
            json.dump(json_cams, file)


def train(args, scene_info, gaussians, train_cameras, gt_socket=None, loss_socket=None, post_socket=None):
    print("🚀Optimizing " + config.scene_name)
    lp, op, pp = parse_args(args)
    dataset, opt, pipe, testing_iterations, saving_iterations, checkpoint_iterations, checkpoint, debug_from = lp.extract(
        args), op.extract(args), pp.extract(
        args), args.test_iterations, args.save_iterations, args.checkpoint_iterations, args.start_checkpoint, args.debug_from

    tb_writer = prepare_output_and_logger(dataset)

    print(f"gt_socket: {gt_socket.__name__ if gt_socket is not None else 'None'}")
    print(f"post_socket: {post_socket.__name__ if post_socket is not None else 'None'}")

    cameras_extent = scene_info.nerf_normalization["radius"]

    # setup gaussian
    gaussians.training_setup(opt)

    # Initialize system state (RNG)
    torch.autograd.set_detect_anomaly(args.detect_anomaly)

    # 开始训练
    bg_color = [1, 1, 1] if dataset.white_background else [0, 0, 0]
    background = torch.tensor(bg_color, dtype=torch.float32, device="cuda")

    iter_start = torch.cuda.Event(enable_timing=True)
    iter_end = torch.cuda.Event(enable_timing=True)

    # first_iter = args.loaded_iter if args.loaded_iter else 0
    first_iter = args.first_iter

    assert opt.iterations > first_iter, "opt.iterations must be larger than loaded_iter"

    viewpoint_stack = None
    ema_loss_for_log = 0.0
    progress_bar = tqdm(range(first_iter, opt.iterations), desc="Training progress")
    first_iter += 1
    for iteration in range(first_iter, opt.iterations + 1):

        iter_start.record()

        gaussians.update_learning_rate(iteration)

        # Every 1000 its we increase the levels of SH up to a maximum degree
        if iteration % 1000 == 0:
            gaussians.oneupSHdegree()

        # Pick a random Camera
        if not viewpoint_stack:
            viewpoint_stack = train_cameras[1.0].copy()
        viewpoint_cam = viewpoint_stack.pop(random.randint(0, len(viewpoint_stack) - 1))

        # Render

        bg = torch.rand((3), device="cuda") if opt.random_background else background

        render_pkg = render(viewpoint_cam, gaussians, pipe, bg)
        image, viewspace_point_tensor, visibility_filter, radii = render_pkg["render"], render_pkg["viewspace_points"], \
            render_pkg["visibility_filter"], render_pkg["radii"]

        # =========== ground truth socket ===============
        if gt_socket is not None:
            gt_image = gt_socket(args=args,
                                 image=image,
                                 iteration=iteration,
                                 gaussians=gaussians,
                                 scene_info=scene_info,
                                 viewpoint_cam=viewpoint_cam, )
        else:
            gt_image = viewpoint_cam.original_image.cuda()

        # Loss
        Ll1 = l1_loss(image, gt_image)
        loss = (1.0 - opt.lambda_dssim) * Ll1 + opt.lambda_dssim * (1.0 - ssim(image, gt_image))

        loss.backward()
        iter_end.record()

        # =============loss socket=======================
        if loss_socket is not None:
            loss_socket(args=args,
                        gt_image=gt_image,
                        image=image,
                        iteration=iteration,
                        gaussians=gaussians,
                        scene_info=scene_info,
                        Ll1=Ll1,
                        loss=loss,
                        viewpoint_cam=viewpoint_cam, )
        # ================================================

        with torch.no_grad():
            # ====================CUSTOM CODE===============
            if post_socket is not None:
                post_socket(args=args,
                            gt_image=gt_image,
                            image=image,
                            iteration=iteration,
                            gaussians=gaussians,
                            scene_info=scene_info,
                            Ll1=Ll1,
                            loss=loss,
                            viewpoint_cam=viewpoint_cam,
                            )
            # ==============================================

            # Progress bar
            ema_loss_for_log = 0.4 * loss.item() + 0.6 * ema_loss_for_log
            if iteration % 10 == 0:
                progress_bar.set_postfix({"Loss": f"{ema_loss_for_log:.{7}f}"})
                progress_bar.update(10)
            if iteration == opt.iterations:
                progress_bar.close()

            # Log and save
            # training_report(tb_writer, iteration, Ll1, loss, l1_loss, iter_start.elapsed_time(iter_end),testing_iterations, scene, render, (pipe, background))
            if (iteration in saving_iterations):
                print("\n[ITER {}] Saving Gaussians".format(iteration))
                # scene.save(iteration)
                point_cloud_path = os.path.join(args.model_path, "point_cloud/iteration_{}".format(iteration))
                gaussians.save_ply(os.path.join(point_cloud_path, "point_cloud.ply"))

            # Densification
            if iteration < opt.densify_until_iter:
                # Keep track of max radii in image-space for pruning
                gaussians.max_radii2D[visibility_filter] = torch.max(gaussians.max_radii2D[visibility_filter],
                                                                     radii[visibility_filter])
                gaussians.add_densification_stats(viewspace_point_tensor, visibility_filter)

                if iteration > opt.densify_from_iter and iteration % opt.densification_interval == 0:
                    size_threshold = 20 if iteration > opt.opacity_reset_interval else None
                    gaussians.densify_and_prune(opt.densify_grad_threshold, 0.005, cameras_extent, size_threshold)

                if iteration % opt.opacity_reset_interval == 0 or (
                        dataset.white_background and iteration == opt.densify_from_iter):
                    gaussians.reset_opacity()

            # Optimizer step
            if iteration < opt.iterations:
                gaussians.optimizer.step()
                gaussians.optimizer.zero_grad(set_to_none=True)

            if iteration in checkpoint_iterations:
                print("\n[ITER {}] Saving Checkpoint".format(iteration))
                torch.save((gaussians.capture(), iteration), args.model_path + "/chkpnt" + str(iteration) + ".pth")
