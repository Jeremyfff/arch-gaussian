import os
import threading
import time
from argparse import Namespace

import imgui

from gui.components import c
from gui.global_app_state import g
from gui.contents.pages.base_page import BasePage
from gui.modules import StyleModule
from scripts.project_manager import ProjectManager
from gui.utils import progress_utils as pu
from gui.user_data import user_settings


class PrepareSharedComponents:
    mLastAddTime = 0

    @classmethod
    def show_input_image_gallery(cls, processing_flag):
        if not ProjectManager.curr_project.get_info('has_input_image_folder'):
            return
        c.image_gallery_with_title(
            title='Input Image Gallery',
            folder_path=ProjectManager.curr_project.get_info('input_image_folder'),
            processing_flag=processing_flag,
            last_add_time=cls.mLastAddTime,
            last_add_time_callback=cls._last_add_time_callback
        )

    @classmethod
    def _last_add_time_callback(cls, lst_add_time):
        cls.mLastAddTime = lst_add_time


class PrepareMainPage(BasePage):
    page_name = 'main'
    page_level = 0

    @classmethod
    def p_init(cls):
        pass

    @classmethod
    def p_call(cls):
        with imgui.font(g.mFontBold):
            imgui.text('PREPARE DATASET')
        if c.icon_text_button('screenshot-2-fill', 'extract video'):
            cls.parent_page_group.switch_page_obj(PrepareExtractVideoPage)
        if c.icon_text_button('earth-line', 'google earth'):
            cls.parent_page_group.switch_page_obj(PrepareGoogleEarthPage)
        if c.icon_text_button('vector-polygon', 'colmap process'):
            cls.parent_page_group.switch_page_obj(PrepareColmapPage)


class PrepareExtractVideoPage(BasePage):
    page_name = 'extract video'
    page_level = 1

    mCurrSelectedMp4Idx = 0
    mExtractTargetFrames = 30
    mExtractIndentFrames = 0
    mExtractingVideo = False

    @classmethod
    def p_init(cls):
        pass

    @classmethod
    def p_call(cls):
        if imgui.button('refresh info'):
            ProjectManager.curr_project.scan_video()
            ProjectManager.curr_project.scan_input_images()
        c.icon_image('video-line', padding=True)
        imgui.same_line()
        imgui.text('from video')
        mp4_file_names = ProjectManager.curr_project.get_info('mp4_file_names')
        mp4_file_paths = ProjectManager.curr_project.get_info('mp4_file_paths')
        if not mp4_file_names:
            imgui.text_wrapped(f'no video detected in {ProjectManager.curr_project.get_info("data_root")}')
            return
        _, cls.mCurrSelectedMp4Idx = imgui.listbox('mp4 files', cls.mCurrSelectedMp4Idx, mp4_file_names)
        imgui.separator()
        c.bold_text('BASIC INFORMATION:')
        imgui.text(f'exist input images = {len(ProjectManager.curr_project.get_info("input_image_names"))}')
        c.bold_text('Target Video File:')
        imgui.text(f'file name: {mp4_file_names[cls.mCurrSelectedMp4Idx]}')
        c.gray_text(f'file path: {mp4_file_paths[cls.mCurrSelectedMp4Idx]}')
        c.easy_tooltip(mp4_file_paths[cls.mCurrSelectedMp4Idx])
        c.bold_text('Parameters:')
        _, cls.mExtractTargetFrames = imgui.input_int('target frames', cls.mExtractTargetFrames)
        _, cls.mExtractIndentFrames = imgui.input_int('indent frames', cls.mExtractIndentFrames)
        c.bold_text('Output Folder:')
        imgui.text(ProjectManager.curr_project.get_info('input_image_folder'))
        if cls.mExtractingVideo:
            StyleModule.push_disabled_button_color()
            imgui.button('EXTRACT FRAMES (RUNNING...)', width=imgui.get_content_region_available_width())
        else:
            StyleModule.push_highlighted_button_color()
            if imgui.button('EXTRACT FRAMES', width=imgui.get_content_region_available_width()):
                threading.Thread(target=cls._extract_video).start()
        StyleModule.pop_button_color()
        pu.p_draw_progress_bar("extract_frames")
        PrepareSharedComponents.show_input_image_gallery(cls.mExtractingVideo)

    @classmethod
    def _extract_video(cls):
        from src.utils.video_utils import extract_frames
        cls.mExtractingVideo = True
        os.makedirs(ProjectManager.curr_project.get_info('input_image_folder'), exist_ok=True)
        ProjectManager.curr_project.scan_input_images()
        pu.p_create_contex("extract_frames", "Extract Frames")
        extract_frames(
            video_path=ProjectManager.curr_project.get_info('mp4_file_paths')[cls.mCurrSelectedMp4Idx],
            target_frames=cls.mExtractTargetFrames,
            indent_frames=cls.mExtractIndentFrames)
        ProjectManager.curr_project.scan_input_images()
        time.sleep(1.1)
        cls.mExtractingVideo = False


class PrepareGoogleEarthPage(BasePage):
    page_name = 'google earth'
    page_level = 1

    mFootageProcessStep = 1
    mFootageResize = False
    mProcessingFootage = False

    @classmethod
    def p_init(cls):
        pass

    @classmethod
    def p_call(cls):
        if imgui.button('refresh info'):
            ProjectManager.curr_project.scan_google_earth_footage()
            ProjectManager.curr_project.scan_input_images()
        if not ProjectManager.curr_project.get_info('has_footage_image_folder'):
            imgui.text('NO GOOGLE EARTH FOOTAGE HERE')
            imgui.text_wrapped(f'add image to {ProjectManager.curr_project.get_info("footage_image_folder")}')
            return
        cls._show_footage_image_gallery()
        input_folder_path = ProjectManager.curr_project.get_info('footage_image_folder')
        output_folder_path = ProjectManager.curr_project.get_info('input_image_folder')
        num_footage = len(ProjectManager.curr_project.get_info('footage_image_names'))
        c.bold_text('INFORMATION')
        imgui.text(f'num footage: {num_footage}')
        imgui.text(f'footage folder: {input_folder_path}')
        c.easy_tooltip(input_folder_path)
        imgui.text(f'output folder: {output_folder_path}')
        c.easy_tooltip(output_folder_path)
        _, cls.mFootageProcessStep = imgui.input_int('step', cls.mFootageProcessStep)
        _, cls.mFootageResize = imgui.checkbox('resize', cls.mFootageResize)
        if cls.mProcessingFootage:
            StyleModule.push_disabled_button_color()
            imgui.button('PROCESSING FOOTAGE (RUNNING...)', width=imgui.get_content_region_available_width())
            pu.p_draw_progress_bar("process_google_earth_frames")
        else:
            StyleModule.push_highlighted_button_color()
            if imgui.button('PROCESS FOOTAGE', width=imgui.get_content_region_available_width()):
                threading.Thread(target=cls._process_footage_frames).start()
        StyleModule.pop_button_color()
        PrepareSharedComponents.show_input_image_gallery(cls.mProcessingFootage)

    @classmethod
    def _show_footage_image_gallery(cls):
        if not ProjectManager.curr_project.get_info('has_footage_image_folder'):
            return
        c.image_gallery_with_title(
            'Footage Image Gallery',
            folder_path=ProjectManager.curr_project.get_info('footage_image_folder'),
        )

    @classmethod
    def _process_footage_frames(cls):
        from src.utils.video_utils import process_google_earth_frames
        cls.mProcessingFootage = True
        os.makedirs(ProjectManager.curr_project.get_info('input_image_folder'), exist_ok=True)
        ProjectManager.curr_project.scan_input_images()
        pu.p_create_contex("process_google_earth_frames", "Process Google Earth Frames")
        process_google_earth_frames(
            input_folder_path=ProjectManager.curr_project.get_info('footage_image_folder'),
            output_folder_path=ProjectManager.curr_project.get_info('input_image_folder'),
            step=cls.mFootageProcessStep,
            resize=cls.mFootageResize
        )
        ProjectManager.curr_project.scan_input_images()
        time.sleep(1.1)
        cls.mProcessingFootage = False




class PrepareColmapPage(BasePage):
    page_name = 'colmap'
    page_level = 1

    mColmapArgs = {}
    mColmapArgTypes = {}
    mColmapDisabledArgs = set()

    mProcessingColmap = False
    mColmapMsgs = []

    @classmethod
    def p_init(cls):
        cls.mColmapArgs = {
            'no_gpu': False,
            'skip_matching': False,
            'source_path': ProjectManager.curr_project.get_info('data_root'),
            'camera': "OPENCV",
            'colmap_executable': user_settings.colmap_executable,
            'resize': False,
            'magick_executable': ""
        }
        cls.mColmapArgTypes = c.get_arg_types(cls.mColmapArgs)
        cls.mColmapDisabledArgs.add('source_path')
        cls.mColmapDisabledArgs.add('magick_executable')
        cls.mColmapDisabledArgs.add('camera')
        cls.mColmapDisabledArgs.add('colmap_executable')
    @classmethod
    def p_call(cls):

        # page 2
        if imgui.button('refresh info'):
            ProjectManager.curr_project.scan_input_images()
            ProjectManager.curr_project.scan_sparse0()
        PrepareSharedComponents.show_input_image_gallery(False)

        c.bold_text('PARAMETERS')
        c.arg_editor(cls.mColmapArgs, cls.mColmapArgTypes, cls.mColmapDisabledArgs)
        if ProjectManager.curr_project.get_info('has_sparse0'):
            imgui.text('already have sparse folder')
        if cls.mProcessingColmap:
            StyleModule.push_disabled_button_color()
            imgui.button('PROCESSING COLMAP (RUNNING...)', width=imgui.get_content_region_available_width())
        else:
            StyleModule.push_highlighted_button_color()
            if imgui.button('PROCESS COLMAP', width=imgui.get_content_region_available_width()):
                threading.Thread(target=cls._process_colmap).start()
        StyleModule.pop_button_color()
        if cls.mColmapMsgs:
            imgui.text(cls.mColmapMsgs[-1])

    @classmethod
    def _process_colmap(cls):

        from src.utils.system_utils import run_command, run_colmap_feature_extraction, run_colmap_matching_block, \
            run_colmap_bundle
        from gui.utils import io_utils

        args = Namespace(
            no_gpu=cls.mColmapArgs['no_gpu'],
            skip_matching=cls.mColmapArgs['skip_matching'],
            source_path=cls.mColmapArgs['source_path'],
            camera=cls.mColmapArgs['camera'],
            colmap_executable=cls.mColmapArgs['colmap_executable'],
            resize=cls.mColmapArgs['resize'],
            magick_executable=cls.mColmapArgs['magick_executable']
        )
        cls.mProcessingColmap = True
        cls.mColmapMsgs = []
        with io_utils.OutputCapture(cls.mColmapMsgs):
            len_files = len(os.listdir(os.path.join(args.source_path, "input")))
            print(f"共有{len_files}个文件")
            colmap_command = '"{}"'.format(args.colmap_executable) if len(args.colmap_executable) > 0 else "colmap"
            print(colmap_command)
            magick_command = '"{}"'.format(args.magick_executable) if len(args.magick_executable) > 0 else "magick"
            print(magick_command)
            use_gpu = 1 if not args.no_gpu else 0
            # matching
            if not args.skip_matching:
                os.makedirs(args.source_path + "/distorted/sparse", exist_ok=True)
            # Feature extraction
            if not args.skip_matching:
                feat_extraction_cmd = colmap_command + " feature_extractor " \
                                                       "--database_path " + args.source_path + "/distorted/database.db \
                        --image_path " + args.source_path + "/input \
                        --ImageReader.single_camera 1 \
                        --ImageReader.camera_model " + args.camera + " \
                        --SiftExtraction.use_gpu " + str(use_gpu)
                print("start feat extraction cmd")
                print(feat_extraction_cmd)
                run_colmap_feature_extraction(feat_extraction_cmd)
            # Feature matching
            if not args.skip_matching:
                feat_matching_cmd = colmap_command + " exhaustive_matcher \
                        --database_path " + args.source_path + "/distorted/database.db \
                        --SiftMatching.use_gpu " + str(use_gpu)
                exit_code = run_colmap_matching_block(feat_matching_cmd)
                if exit_code != 0:
                    print(f"Feature matching failed with code {exit_code}.")
                    cls._exit_process_colmap()
                    return

            # Bundle adjustment
            if not args.skip_matching:
                # The default Mapper tolerance is unnecessarily large,
                # decreasing it speeds up bundle adjustment steps.
                mapper_cmd = (colmap_command + " mapper \
                        --database_path " + args.source_path + "/distorted/database.db \
                        --image_path " + args.source_path + "/input \
                        --output_path " + args.source_path + "/distorted/sparse \
                        --Mapper.ba_global_function_tolerance=0.000001")
                exit_code = run_colmap_bundle(mapper_cmd, len_files)
                if exit_code:
                    print(f"Mapper failed with code {exit_code}.")
                    cls._exit_process_colmap()
                    return
                print("done.")
            # Image undistortion
            # We need to undistort our images into ideal pinhole intrinsics.
            img_undistortion_cmd = (colmap_command + " image_undistorter \
                    --image_path " + args.source_path + "/input \
                    --input_path " + args.source_path + "/distorted/sparse/0 \
                    --output_path " + args.source_path + "\
                    --output_type COLMAP")
            exit_code = run_command(img_undistortion_cmd)
            if exit_code:
                print(f"Mapper failed with code {exit_code}")
                cls._exit_process_colmap()
                return

            import shutil
            import logging
            files = os.listdir(args.source_path + "/sparse")
            os.makedirs(args.source_path + "/sparse/0", exist_ok=True)
            # Copy each file from the source directory to the destination directory
            for file in files:
                if file == '0':
                    continue
                source_file = os.path.join(args.source_path, "sparse", file)
                destination_file = os.path.join(args.source_path, "sparse", "0", file)
                shutil.move(source_file, destination_file)

            if args.resize:
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
        ProjectManager.curr_project.scan_sparse0()
        cls._exit_process_colmap()

    @classmethod
    def _exit_process_colmap(cls):
        cls.mProcessingColmap = False


class PrepareLevel2Page(BasePage):
    page_name = 'level2'
    page_level = 2

    @classmethod
    def p_init(cls):
        pass

    @classmethod
    def p_call(cls):
        imgui.text('level2')
