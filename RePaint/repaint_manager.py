import os
import argparse
import threading
import traceback

import torch
import torch as th
import torch.nn.functional as F
import time
from RePaint import conf_mgt
from RePaint.utils import yamlread
from RePaint.guided_diffusion import dist_util

from RePaint.guided_diffusion.script_util import (
    NUM_CLASSES,
    model_and_diffusion_defaults,
    classifier_defaults,
    create_model_and_diffusion,
    create_classifier,
    select_args,
)  # noqa: E402


class RepaintManager:
    def __init__(self, conf_path="./Repaint/confs/test.yml"):
        self.conf_arg = conf_mgt.conf_base.Default_Conf()
        self.conf_arg.update(yamlread(conf_path))

        conf = self.conf_arg
        print("Start", conf['name'])
        self.device = dist_util.dev(conf.get('device'))

        self.model, self.diffusion = create_model_and_diffusion(
            **select_args(conf, model_and_diffusion_defaults().keys()), conf=conf
        )
        self.model.load_state_dict(
            dist_util.load_state_dict(os.path.expanduser(
                conf.model_path), map_location="cpu")
        )
        self.model.to(self.device)
        if conf.use_fp16:
            self.model.convert_to_fp16()
        self.model.eval()

        self.show_progress = conf.show_progress
        self.cond_fn = None  # we do not support cond_fn here

        # self.dl = conf.get_dataloader(dset='eval', dsName=conf.get_default_eval_name())

    def raw_run(self):
        """
        论文的原始方法
        :return:
        """
        conf = self.conf_arg
        print("Start", conf['name'])

        device = dist_util.dev(conf.get('device'))

        model, diffusion = create_model_and_diffusion(
            **select_args(conf, model_and_diffusion_defaults().keys()), conf=conf
        )
        model.load_state_dict(
            dist_util.load_state_dict(os.path.expanduser(
                conf.model_path), map_location="cpu")
        )
        model.to(device)
        if conf.use_fp16:
            model.convert_to_fp16()
        model.eval()

        show_progress = conf.show_progress
        cond_fn = None

        def model_fn(x, t, y=None, gt=None, **kwargs):
            assert y is not None
            return model(x, t, y if conf.class_cond else None, gt=gt)

        print("sampling...")
        all_images = []

        dset = 'eval'

        eval_name = conf.get_default_eval_name()

        dl = conf.get_dataloader(dset=dset, dsName=eval_name)

        for batch in iter(dl):

            for k in batch.keys():
                if isinstance(batch[k], th.Tensor):
                    batch[k] = batch[k].to(device)

            model_kwargs = {}

            model_kwargs["gt"] = batch['GT']

            gt_keep_mask = batch.get('gt_keep_mask')
            if gt_keep_mask is not None:
                model_kwargs['gt_keep_mask'] = gt_keep_mask

            batch_size = model_kwargs["gt"].shape[0]

            if conf.cond_y is not None:
                classes = th.ones(batch_size, dtype=th.long, device=device)
                model_kwargs["y"] = classes * conf.cond_y
            else:
                classes = th.randint(
                    low=0, high=NUM_CLASSES, size=(batch_size,), device=device
                )
                model_kwargs["y"] = classes

            sample_fn = (
                diffusion.p_sample_loop if not conf.use_ddim else diffusion.ddim_sample_loop
            )

            result = sample_fn(
                model_fn,
                (batch_size, 3, conf.image_size, conf.image_size),
                clip_denoised=conf.clip_denoised,
                model_kwargs=model_kwargs,
                cond_fn=cond_fn,
                device=device,
                progress=show_progress,
                return_all=True,
                conf=conf
            )
            srs = self.toU8(result['sample'])
            gts = self.toU8(result['gt'])
            lrs = self.toU8(result.get('gt') * model_kwargs.get('gt_keep_mask') + (-1) *
                            th.ones_like(result.get('gt')) * (1 - model_kwargs.get('gt_keep_mask')))

            gt_keep_masks = self.toU8((model_kwargs.get('gt_keep_mask') * 2 - 1))

            conf.eval_imswrite(
                srs=srs, gts=gts, lrs=lrs, gt_keep_masks=gt_keep_masks,
                img_names=batch['GT_name'], dset=dset, name=eval_name, verify_same=False)

        print("sampling complete")

    @staticmethod
    def toU8(sample):
        if sample is None:
            return sample

        sample = ((sample + 1) * 127.5).clamp(0, 255).to(th.uint8)
        sample = sample.permute(0, 2, 3, 1)
        sample = sample.contiguous()
        sample = sample.detach().cpu().numpy()
        return sample

    @staticmethod
    def _extract_into_tensor(arr, timesteps, broadcast_shape):
        """
        Extract values from a 1-D numpy array for a batch of indices.

        :param arr: the 1-D numpy array.
        :param timesteps: a tensor of indices into the array to extract.
        :param broadcast_shape: a larger shape of K dimensions with the batch
                                dimension equal to the length of timesteps.
        :return: a tensor of shape [batch_size, 1, ...] where the shape has K dims.
        """
        res = th.from_numpy(arr).to(device=timesteps.device)[timesteps].float()
        while len(res.shape) < len(broadcast_shape):
            res = res[..., None]
        return res.expand(broadcast_shape)


    def debug_get_gt_and_gt_keep_mask(self):
        """
        测试代码，临时获得gt 和 gt mask
        :return:
        """
        conf = self.conf_arg
        dl = conf.get_dataloader(dset='eval', dsName=conf.get_default_eval_name())
        batch = next(iter(dl))
        gt = batch['GT']
        gt_keep_mask = batch['gt_keep_mask']

        return gt, gt_keep_mask

    @property
    def total_T(self):
        return self.conf_arg.schedule_jump_params['t_T']

    def take_one_sample(self, gt: th.Tensor, gt_keep_mask: th.Tensor,
                        image_after_step: th.Tensor,
                        t: int):
        """

        :param t:
        :param image_after_step: can be None
        :param gt: torch.Tensor(1, 3, 256, 256) by default, -1 to 1
        :param gt_keep_mask:
        :return:
        """
        conf = self.conf_arg

        # upload gt and gt_keep_mask to device
        gt = gt.to(self.device)
        gt_keep_mask = gt_keep_mask.to(self.device)

        if image_after_step is None:
            image_after_step = th.randn_like(gt, device=self.device)
        else:
            image_after_step = image_after_step.to(self.device)
        # generate model kwargs
        model_kwargs = {
            "gt": gt,
            'gt_keep_mask': gt_keep_mask,
            'y': None  # we assume conf.class_cond is false and self.conf_fn is None
        }
        # get batch_size
        shape = gt.shape

        # we use self.diffusion.p_sample_loop as sample_fn

        t: th.Tensor = th.tensor([t] * shape[0], device=self.device)

        # enter p_sample function
        with th.no_grad():
            noise = th.randn_like(image_after_step, device=self.device)
            alpha_cumprod = self._extract_into_tensor(self.diffusion.alphas_cumprod, t, image_after_step.shape)

            # we assume if conf.inpa_inj_sched_prev_cumnoise is false in conf
            gt_weight = th.sqrt(alpha_cumprod)
            # print(f"gt_weight device = {gt_weight.device}")
            # print(f"gt device = {gt.device}")
            gt_part = gt_weight * gt

            noise_weight = th.sqrt((1 - alpha_cumprod))
            noise_part = noise_weight * th.randn_like(image_after_step)

            weighed_gt = gt_part + noise_part

            x = (
                    gt_keep_mask * weighed_gt
                    +
                    (1 - gt_keep_mask) * image_after_step
            )

            out = self.diffusion.p_mean_variance(
                self.model,
                x,
                t,
                clip_denoised=None,
                denoised_fn=None,
                model_kwargs=model_kwargs,
            )
            # out.keys() = dict_keys(['mean', 'variance', 'log_variance', 'pred_xstart'])
            pred_xstart = out['pred_xstart']

            nonzero_mask = (
                (t != 0).float().view(-1, *([1] * (len(x.shape) - 1)))
            )

            sample = out["mean"] + nonzero_mask * th.exp(0.5 * out["log_variance"]) * noise
            part2 = nonzero_mask * th.exp(0.5 * out["log_variance"]) * noise
        return sample, pred_xstart, out, noise, part2
