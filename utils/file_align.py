import os
import shutil

BASE_DIR = "scene_1_unaligned"
TARGET_DIR = "scene_1"
os.makedirs(TARGET_DIR, exist_ok=True)

# 固定要处理的文件夹
FOLDERS = [
    "LIDAR_FRONT",
    "LIDAR_REAR",
    "LIDAR_TOP_32",
    "CAM_FRONT_8M",
    "CAM_FRONT_3M",
    "CAM_LEFT_3M",
    "CAM_RIGHT_3M",
    "CAM_BACK_3MH"
]

def truncate_timestamp(fname):
    """
    输入: 1758683129000352232.png
    输出: 1758683129.png   (去掉最后9位)
    """
    base, ext = os.path.splitext(fname)
    if len(base) > 9:
        base = base[:-9]  # 去掉最后9位
    return base + ext

def process_folder(folder):
    src_dir = os.path.join(BASE_DIR, folder)
    dst_dir = os.path.join(TARGET_DIR, folder)
    os.makedirs(dst_dir, exist_ok=True)

    for fname in os.listdir(src_dir):
        old_path = os.path.join(src_dir, fname)
        if not os.path.isfile(old_path):
            continue
        new_name = truncate_timestamp(fname)
        new_path = os.path.join(dst_dir, new_name)
        shutil.copy2(old_path, new_path)

        print(f"{old_path} -> {new_path}")

def main():
    for folder in FOLDERS:
        process_folder(folder)

if __name__ == "__main__":
    main()
