
import os
from src.utils.video_utils import extract_frames
import logging
import subprocess
from argparse import ArgumentParser, Namespace
import shutil
import config
def run_command(command):
    try:
        result = subprocess.check_output(command, shell=True, encoding='utf-8')
        print(result)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        exit()

def process_colmap(args: Namespace):
    colmap_command = '"{}"'.format(args.colmap_executable) if len(args.colmap_executable) > 0 else "colmap"
    print(colmap_command)
    magick_command = '"{}"'.format(args.magick_executable) if len(args.magick_executable) > 0 else "magick"
    use_gpu = 1 if not args.no_gpu else 0

    if not args.skip_matching:
        os.makedirs(args.source_path + "/distorted/sparse", exist_ok=True)

        ## Feature extraction
        feat_extracton_cmd = colmap_command + " feature_extractor " \
                                              "--database_path " + args.source_path + "/distorted/database.db \
                --image_path " + args.source_path + "/input \
                --ImageReader.single_camera 1 \
                --ImageReader.camera_model " + args.camera + " \
                --SiftExtraction.use_gpu " + str(use_gpu)
        print("start feat extraction cmd")
        print(feat_extracton_cmd)
        run_command(feat_extracton_cmd)
        # exit_code = os.system(feat_extracton_cmd)
        # if exit_code != 0:
        #    logging.error(f"Feature extraction failed with code {exit_code}. Exiting.")
        #    exit(exit_code)

        ## Feature matching
        feat_matching_cmd = colmap_command + " exhaustive_matcher \
                --database_path " + args.source_path + "/distorted/database.db \
                --SiftMatching.use_gpu " + str(use_gpu)
        exit_code = os.system(feat_matching_cmd)
        if exit_code != 0:
            logging.error(f"Feature matching failed with code {exit_code}. Exiting.")
            exit(exit_code)

        ### Bundle adjustment
        # The default Mapper tolerance is unnecessarily large,
        # decreasing it speeds up bundle adjustment steps.
        mapper_cmd = (colmap_command + " mapper \
                --database_path " + args.source_path + "/distorted/database.db \
                --image_path " + args.source_path + "/input \
                --output_path " + args.source_path + "/distorted/sparse \
                --Mapper.ba_global_function_tolerance=0.000001")
        exit_code = os.system(mapper_cmd)
        if exit_code != 0:
            logging.error(f"Mapper failed with code {exit_code}. Exiting.")
            exit(exit_code)

    ### Image undistortion
    ## We need to undistort our images into ideal pinhole intrinsics.
    img_undist_cmd = (colmap_command + " image_undistorter \
            --image_path " + args.source_path + "/input \
            --input_path " + args.source_path + "/distorted/sparse/0 \
            --output_path " + args.source_path + "\
            --output_type COLMAP")
    exit_code = os.system(img_undist_cmd)
    if exit_code != 0:
        logging.error(f"Mapper failed with code {exit_code}. Exiting.")
        exit(exit_code)

    files = os.listdir(args.source_path + "/sparse")
    os.makedirs(args.source_path + "/sparse/0", exist_ok=True)
    # Copy each file from the source directory to the destination directory
    for file in files:
        if file == '0':
            continue
        source_file = os.path.join(args.source_path, "sparse", file)
        destination_file = os.path.join(args.source_path, "sparse", "0", file)
        shutil.move(source_file, destination_file)

    if (args.resize):
        print("Copying and resizing...")

        # Resize images.
        os.makedirs(args.source_path + "/images_2", exist_ok=True)
        os.makedirs(args.source_path + "/images_4", exist_ok=True)
        os.makedirs(args.source_path + "/images_8", exist_ok=True)
        # Get the list of files in the source directory
        files = os.listdir(args.source_path + "/images")
        # Copy each file from the source directory to the destination directory
        for file in files:
            source_file = os.path.join(args.source_path, "images", file)

            destination_file = os.path.join(args.source_path, "images_2", file)
            shutil.copy2(source_file, destination_file)
            exit_code = os.system(magick_command + " mogrify -resize 50% " + destination_file)
            if exit_code != 0:
                logging.error(f"50% resize failed with code {exit_code}. Exiting.")
                exit(exit_code)

            destination_file = os.path.join(args.source_path, "images_4", file)
            shutil.copy2(source_file, destination_file)
            exit_code = os.system(magick_command + " mogrify -resize 25% " + destination_file)
            if exit_code != 0:
                logging.error(f"25% resize failed with code {exit_code}. Exiting.")
                exit(exit_code)

            destination_file = os.path.join(args.source_path, "images_8", file)
            shutil.copy2(source_file, destination_file)
            exit_code = os.system(magick_command + " mogrify -resize 12.5% " + destination_file)
            if exit_code != 0:
                logging.error(f"12.5% resize failed with code {exit_code}. Exiting.")
                exit(exit_code)

    print("Done.")


def main():
    print(f"source path = {config.args.source_path}")
    print("[-] STEP 1")
    if not os.path.exists(os.path.join(config.args.source_path, "input")):
        success, frames_folder = extract_frames(os.path.join(config.args.source_path, config.vid_name), config.vid_frames)
        if not success:
            exit(1)
    else:
        print("[!]检测到抽帧已完成，已为您跳过")

    print("[-] STEP 2")
    process_colmap(config.colmap_args)


if __name__ == '__main__':

    main()
