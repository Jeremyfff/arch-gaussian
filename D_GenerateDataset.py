import shutil

import numpy as np
import os
from PIL import Image
from tqdm import tqdm
from transformers import pipeline

captioner = pipeline("image-to-text",model="Salesforce/blip-image-captioning-base")

input_folder = r"src\UnityGaussianSplatting\projects\GaussianExample-URP\output"
output_folder = r"dataset\SD\NewYorkCity"


def main():
    gt_folder = os.path.join(output_folder, "gt")
    mask_folder = os.path.join(output_folder, "mask")
    label_folder = os.path.join(output_folder, "label")

    if not os.path.exists(gt_folder):
        os.makedirs(gt_folder)
    if not os.path.exists(mask_folder):
        os.makedirs(mask_folder)
    if not os.path.exists(label_folder):
        os.makedirs(label_folder)
    # init
    gt_imgs = []
    mask1_imgs = []
    mask2_imgs = []
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            file_path = os.path.join(root, file)
            # 在这里你可以对文件做任何操作，比如打印文件路径
            if file.endswith('gt.jpg'):
                gt_imgs.append(file_path)
            elif file.endswith('mask1.jpg'):
                mask1_imgs.append(file_path)
            elif file.endswith('mask2.jpg'):
                mask2_imgs.append(file_path)
    assert len(gt_imgs) == len(mask1_imgs) == len(mask2_imgs), "文件数量不匹配"

    # convert
    for i in tqdm(range(len(mask1_imgs))):
        mask1 = np.array(Image.open(mask1_imgs[i]).convert("L")) / 255.0
        mask2 = np.array(Image.open(mask2_imgs[i]).convert("L")) / 255.0

        mask = mask1 * mask2
        mask *= 255.0
        result_image = Image.fromarray(mask.astype(np.uint8))
        result_image.save(os.path.join(mask_folder, f"{i:05d}.jpg"))

        label = captioner(Image.open(gt_imgs[i]))
        # print(label[0]['generated_text'])
        with open(os.path.join(label_folder, f"{i:05d}.txt"), 'w') as f:
            f.write(label[0]['generated_text'])

        shutil.copy2(gt_imgs[i], os.path.join(gt_folder, f"{i:05d}.jpg"))
if __name__ == "__main__":
    main()