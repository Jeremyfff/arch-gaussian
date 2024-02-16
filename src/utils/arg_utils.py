from argparse import ArgumentParser, Namespace
from arguments import ModelParams, PipelineParams, OptimizationParams


def parse_args(args):
    # Set up command line argument parser
    parser = ArgumentParser(description="Training script parameters")
    dataset = ModelParams(parser)
    opt = OptimizationParams(parser)
    pipe = PipelineParams(parser)

    dataset.sh_degree = args.sh_degree
    dataset.source_path = args.source_path
    dataset.model_path = args.model_path
    dataset.images = args.images
    dataset.resolution = args.resolution
    dataset.white_background = args.white_background
    dataset.data_device = args.data_device
    dataset.eval = args.eval

    opt.iterations = args.iterations
    opt.position_lr_init = args.position_lr_init
    opt.position_lr_final = args.position_lr_final
    opt.position_lr_delay_mult = args.position_lr_delay_mult
    opt.position_lr_max_steps = args.position_lr_max_steps
    opt.feature_lr = args.feature_lr
    opt.opacity_lr = args.opacity_lr
    opt.scaling_lr = args.scaling_lr
    opt.rotation_lr = args.rotation_lr
    opt.percent_dense = args.percent_dense
    opt.lambda_dssim = args.lambda_dssim
    opt.densification_interval = args.densification_interval
    opt.opacity_reset_interval = args.opacity_reset_interval
    opt.densify_from_iter = args.densify_from_iter
    opt.densify_until_iter = args.densify_until_iter
    opt.densify_grad_threshold = args.densify_grad_threshold
    opt.random_background = args.random_background

    pipe.convert_SHs_python = args.convert_SHs_python
    pipe.compute_cov3D_python = args.compute_cov3D_python
    pipe.debug = args.debug
    return dataset, opt, pipe