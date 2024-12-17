import os.path

import torch as th
import torchvision.transforms as transforms
from PIL import Image, ImageDraw, ImageFont

def save_images(img1:th.Tensor,
                img2: th.Tensor,
                img1_name:str,
                img2_name:str,
                save_path:str):
    folder = os.path.dirname(save_path)
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    # 创建转换函数，将 tensor 转换为 PIL 图像
    tensor_to_pil = transforms.ToPILImage()

    img11 = img1 * 0.5 + 0.5
    img22 = img2 * 0.5 + 0.5
    img11 = th.clamp(img11, 0, 1)
    img22 = th.clamp(img22, 0, 1)
    # 创建两个 PIL 图像对象
    pil_image1 = tensor_to_pil(img11.squeeze(0))
    pil_image2 = tensor_to_pil(img22.squeeze(0))

    # 在图像上写上名字
    font = ImageFont.load_default()
    draw1 = ImageDraw.Draw(pil_image1)
    draw2 = ImageDraw.Draw(pil_image2)

    draw1.text((10, 10), img1_name, font=font, fill=(255, 255, 255, 128))
    draw2.text((10, 10), img2_name, font=font, fill=(255, 255, 255, 128))

    # 创建一个新的图片，将两张图片拼接在一起
    combined_image = Image.new('RGB', (512, 256))
    combined_image.paste(pil_image1, (0, 0))
    combined_image.paste(pil_image2, (256, 0))

    # 保存拼接后的图片到本地
    combined_image.save(save_path)