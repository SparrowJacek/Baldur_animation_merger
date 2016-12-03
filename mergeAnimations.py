import math
import ntpath
import os
import re
import struct
import subprocess
import sys

# This program uses Imagemagick for making batch changes to images

def get_coordinate_offset(image1_coordinate, image2_coordinate, anim1_offset, anim2_offset):
    coordinate_offset = math.ceil((image2_coordinate - image1_coordinate) / 2 + anim1_offset - anim2_offset)
    if coordinate_offset >= 0:
        return ('+' + str(coordinate_offset))
    else:
        return str(coordinate_offset)


def change_image_color(colors_pair, imagefile, im_mogrify_path):
    try:
        subprocess.call([im_mogrify_path, '-fill', colors_pair[0], '-opaque', colors_pair[1], imagefile],
                        shell=True)
    except:
        print('Your path to mogrify.exe is wrong, please edit config.txt')
        input('Press any key to close')
        sys.exit(0)


def merge_images(image1file, image2file, output_filename, current_image1_metadata, current_image2_metadata,
                 im_convert_path):
    try:
        subprocess.call(
            [im_convert_path, image1file, '-gravity', 'center', '-background', 'none',
             '-extent', '250x250', image2file, '-gravity', 'center', '-geometry',
             get_coordinate_offset(current_image1_metadata[0], current_image2_metadata[0], current_image1_metadata[2],
                                   current_image2_metadata[2]) + get_coordinate_offset(current_image1_metadata[1],
                                                                                       current_image2_metadata[1],
                                                                                       current_image1_metadata[3],
                                                                                   current_image2_metadata[3]),
            '-composite', '-mosaic', '-trim', output_filename], shell=True)
    except:
        print('Your path to convert.exe is wrong, please edit config.txt')
        input('Press any key to close')
        sys.exit(0)

def create_anim_metadata(filename):
    result = []
    with open(filename, 'rb') as f:
        f.read(8)  # skip first 8 bytes
        (frames_count,) = struct.unpack('<H', f.read(2))
        f.read(2)  # omit number of cycles and color index
        (frames_start_offset,) = struct.unpack('<I', f.read(4))
        f.seek(frames_start_offset)
        for i in range(frames_count):
            (x,) = struct.unpack('<H', f.read(2))
            (y,) = struct.unpack('<H', f.read(2))
            (x_offset,) = struct.unpack('<h', f.read(2))
            (y_offset,) = struct.unpack('<h', f.read(2))
            f.read(4)  # skip offset to frame data
            result.append((x, y, x_offset, y_offset))
    return result


def read_image_filenames(dir, filename_prefix):
    compiled_filename_patttern = re.compile(filename_prefix + "([0-9]*)\.png", re.IGNORECASE)
    images_dict = {}
    for file in os.listdir(dir):
        match = compiled_filename_patttern.match(file)
        if match:
            images_dict[int(match.group(1))] = os.path.abspath(os.path.join(dir, file))
    return images_dict


def create_image_series(anim1_images_dict, anim2_images_dict, anim1_metadata, anim2_metadata, colors_map,
                        im_mogrify_path,
                        im_convert_path):
    result_directory = os.path.join(ntpath.dirname(list(anim1_images_dict.values())[0]), 'result')
    if not os.path.exists(result_directory):
        os.makedirs(result_directory)
    for frame_number in anim1_images_dict:
        output_filename = ntpath.join(result_directory, ntpath.basename(anim1_images_dict[frame_number]))
        for colors_pair in colors_map:
            change_image_color(colors_pair, anim2_images_dict[frame_number], im_mogrify_path)

        merge_images(anim1_images_dict[frame_number], anim2_images_dict[frame_number],
                     os.path.join(result_directory, ntpath.basename(anim1_images_dict[frame_number])),
                     anim1_metadata[frame_number], anim2_metadata[frame_number], im_convert_path)


if __name__ == '__main__':
    with open('config.txt', 'r') as config_file:
        im_identify_path = config_file.readline().strip()
        im_convert_path = config_file.readline().strip()
        im_mogrify_path = config_file.readline().strip()
    colors_map = [("rgb(255,255,246)", "rgb(246,255,246)"),
                  ("rgb(255,255,209)", "rgb(209,255,209)"),
                  ("rgb(255,255,177)", "rgb(177,255,177)"),
                  ("rgb(255,255,145)", "rgb(113,255,113)"),
                  ("rgb(255,255,17)", "rgb(17,255,17)"),
                  ("rgb(209,209,0)", "rgb(0,209,0)"),
                  ("rgb(144,144,0)", "rgb(0,144,0)"),
                  ("rgb(176,176,0)", "rgb(0,176,0)"),
                  ("rgb(112,112,0)", "rgb(0,112,0)"),
                  ("rgb(240,240,0)", "rgb(0,240,0)"),
                  ("rgb(80,80,0)", "rgb(0,80,0)"),
                  ("rgb(64,64,0)", "rgb(0,64,0)")]
    anim1_images_path = os.path.abspath(sys.argv[1])
    anim1_path = os.path.abspath(sys.argv[2])
    anim1_images_prefix = ntpath.basename(anim1_path).split('.')[0]
    anim2_images_path = os.path.abspath(sys.argv[3])
    anim2_path = os.path.abspath(sys.argv[4])
    anim2_images_prefix = ntpath.basename(anim2_path).split('.')[0]
    anim1_images_dict = read_image_filenames(anim1_images_path, anim1_images_prefix)
    anim2_images_dict = read_image_filenames(anim2_images_path, anim2_images_prefix)


    anim1_metadata = create_anim_metadata(anim1_path)
    anim2_metadata = create_anim_metadata(anim2_path)


    create_image_series(anim1_images_dict, anim2_images_dict, anim1_metadata, anim2_metadata, colors_map,
                        im_mogrify_path, im_convert_path)


#