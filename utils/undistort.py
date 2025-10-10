import cv2
import numpy as np
import os
import glob
import re
from pathlib import Path
from itertools import chain
import json
import argparse

def update_camera_config(camera_config_path, param_files, input_dirs):
    # 初始化空的配置数组
    camera_config = []

    # 加载外部参数
    with open('utils/32m2cameras.json', 'r') as f:
        ext_params = json.load(f)

    # 遍历每个相机配置
    for i, (param_file, input_dir) in enumerate(zip(param_files, input_dirs)):
        if input_dir==f"{scene_dir}/CAM_FRONT_8M":
            width=3840
            height=2160
        else:
            width=1920
            height=1536
        internal_params = read_camera_parameters(param_file)
        fx = internal_params.get("FX")
        fy = internal_params.get("FY")
        cx = internal_params.get("CX")
        cy = internal_params.get("CY")
        # 获取外参
        external_matrix = ext_params.get(input_dir.split('/')[-1])
        flat_external = sum(external_matrix, [])  # 展平为一维列表

        # 构建单个相机配置
        camera_entry = {
            "camera_internal": {
                "fx": fx,
                "fy": fy,
                "cx": cx,
                "cy": cy
            },
            "width": width,
            "height": height,
            "camera_external": flat_external,
            "rowMajor": True
        }

        # 添加到配置列表
        camera_config.append(camera_entry)

    # 写入新文件
    with open(camera_config_path, 'w') as f:
        json.dump(camera_config, f, indent=4)

    print(f"✅ 已成功创建并写入 {camera_config_path}")

def generate_camera_config_dir(camera_config_path):
    with open(camera_config_path, "r") as f:
        data = json.load(f)

    # 创建 camera_config 文件夹
    os.makedirs(f"{scene_dir}/camera_config", exist_ok=True)

    # 获取 LIDAR_CONCAT 下的所有 .pcd 文件名（去掉后缀）
    pcd_files = [f for f in os.listdir(f"{scene_dir}/lidar_point_cloud_0") if f.endswith(".pcd")]
    base_names = [os.path.splitext(f)[0] for f in pcd_files]

    # 为每个文件名生成对应的 .json 文件，并写入相同的内容
    for name in base_names:
        json_path = os.path.join(scene_dir, "camera_config", f"{name}.json")
        with open(json_path, "w") as json_file:
            json.dump(data, json_file, indent=4)

    print("✅ 所有 JSON 文件已生成并保存到 camera_config 文件夹中。")

def read_camera_parameters(param_file):
    """从参数文件中读取相机内参和畸变系数"""
    params = {}
    with open(param_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines:
        # 使用冒号分割键值
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # 忽略值为'/'或'null'的参数
            if value != '/' and value != 'null' and value != '':
                try:
                    # 尝试将值转换为浮点数
                    params[key] = float(value)
                except ValueError:
                    # 如果不能转换为浮点数，则保存为字符串
                    params[key] = value
    
    return params

def undistort_fisheye_images(param_file, input_dir, output_dir):
    """对鱼眼相机拍摄的图像进行去畸变处理"""
    # 读取参数
    params = read_camera_parameters(param_file)
    
    # 提取相机内参
    fx = params.get('FX')
    fy = params.get('FY')
    cx = params.get('CX')
    cy = params.get('CY')
    
    # 提取畸变系数
    k1 = params.get('K1', 0.0)
    k2 = params.get('K2', 0.0)
    k3 = params.get('K3', 0.0)
    k4 = params.get('K4', 0.0)
    
    # 检查必要的参数是否存在
    required_params = ['FX', 'FY', 'CX', 'CY']
    if not all(param in params for param in required_params):
        missing = [param for param in required_params if param not in params]
        raise ValueError(f"缺少必要的相机参数: {', '.join(missing)}")
    
    # 创建相机矩阵
    camera_matrix = np.array([
        [fx, 0, cx],
        [0, fy, cy],
        [0, 0, 1]
    ])
    
    # 畸变系数 (k1, k2, p1, p2, k3, k4, k5, k6)
    # OpenCV的鱼眼相机模型使用k1, k2, k3, k4作为畸变系数
    dist_coeffs = np.array([k1, k2, k3, k4])
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取输入目录中的所有图像
    image_files = glob.glob(os.path.join(input_dir, '*.png')) + glob.glob(os.path.join(input_dir, '*.jpg'))
    
    # 处理每个图像
    for image_file in image_files:
        # 读取图像
        img = cv2.imread(image_file)
        if img is None:
            print(f"无法读取图像: {image_file}")
            continue
        
        # 获取图像尺寸
        h, w = img.shape[:2]
        
        # 计算新的相机矩阵
        new_camera_matrix = camera_matrix.copy()
        
        # 使用OpenCV的鱼眼相机模型进行去畸变
        map1, map2 = cv2.fisheye.initUndistortRectifyMap(
            camera_matrix, 
            dist_coeffs, 
            np.eye(3), 
            new_camera_matrix, 
            (w, h), 
            cv2.CV_16SC2
        )
        undistorted_img = cv2.remap(img, map1, map2, interpolation=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
        
        # 打印去畸变后的图像尺寸
        # print(f"去畸变后的图像尺寸: {undistorted_img.shape[1]}x{undistorted_img.shape[0]}")
        
        # 构建输出文件路径
        filename = os.path.basename(image_file)
        output_file = os.path.join(output_dir, filename)
        
        # 保存去畸变后的图像
        cv2.imwrite(output_file, undistorted_img)
        print(f"已处理: {image_file}")

def crop_image(image, cx, cy, crop_percent=1):
    """从光学中心裁剪图像"""
    width=3840
    height=2160
    
    # 计算裁剪区域
    crop_width = 1920  # 直接指定目标宽度
    crop_height = 1536  # 直接指定目标高度
    
    # 计算裁剪区域的边界（从中心开始）
    left = int((width - crop_width) / 2)
    right = left + crop_width
    top = int((height - crop_height) / 2)
    bottom = top + crop_height
    
    # 裁剪图像
    cropped = image[top:bottom, left:right]
    # print(f"\n裁剪后的图像尺寸: {cropped.shape[1]}x{cropped.shape[0]}")
    return cropped

def calculate_new_camera_matrix(params, input_dir, crop_percent=1):
    """计算裁剪后的相机内参矩阵"""
    fx = params.get('FX')
    fy = params.get('FY')
    cx = params.get('CX')
    cy = params.get('CY')
    
    # 读取一张图片来获取尺寸，支持jpg和png格式
    input_path = Path(input_dir)
    sample_image = next(chain(input_path.glob("*.jpg"), input_path.glob("*.png")), None)
    if sample_image:
        image = cv2.imread(str(sample_image))
        if image is not None:
            width=3840
            height=2160

            
            # 计算裁剪区域
            crop_width = width-1920
            crop_height = height-1536
            # 计算裁剪边界
            left = max(0, int(crop_width/2))
            top = max(0, int(crop_height/2))
            
            # 计算裁剪后的主点坐标
            # 新的主点坐标需要减去裁剪的偏移量
            new_cx = cx - left  # left是裁剪的起始x坐标
            new_cy = cy - top   # top是裁剪的起始y坐标
            print(f"新的主点坐标: {new_cx}, {new_cy}")
            # 构建原始相机矩阵
            camera_matrix = np.array([
                [fx, 0, cx],
                [0, fy, cy],
                [0, 0, 1]
            ])
            
            # 构建新的相机矩阵
            new_camera_matrix = np.array([
                [fx, 0, new_cx],
                [0, fy, new_cy],
                [0, 0, 1]
            ])
            
            return camera_matrix, new_camera_matrix
    
    return None, None

def process_fisheye_camera(param_file, input_dir, output_dir):
    try:
        print(f'开始处理camera: {input_dir}中的图片')
        undistort_fisheye_images(param_file, input_dir, output_dir)
        print(f"所有图像已处理完成并保存到 {output_dir} 目录")
    except Exception as e:
        print(f"处理出错: {e}")

def undistort_pinhole_image(image_path, params, input_dir):
    # 读取图像
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法读取图像: {image_path}")

    # 获取原始图像尺寸
    h, w = img.shape[:2]
    
    # 构建相机矩阵
    camera_matrix = np.array([
        [params['FX'], 0, params['CX']],
        [0, params['FY'], params['CY']],
        [0, 0, 1]
    ])
    
    # 构建畸变系数
    dist_coeffs = np.array([
        params['K1'], params['K2'], params['P1'], params['P2'],
        params['K3'], params['K4'], params['K5'], params['K6']
    ])
    
    # 去畸变
    undistorted_img = cv2.undistort(img, camera_matrix, dist_coeffs)
        
    return undistorted_img, camera_matrix

def process_pinhole_image(param_file, input_dir, output_dir):
        try:
            params = read_camera_parameters(param_file)
            image_files = glob.glob(os.path.join(input_dir, '*.jpg'))+glob.glob(os.path.join(input_dir, '*.png'))
            # 处理所有图片
            for image_path in image_files:
                try:
                    cropped_img, new_camera_matrix = undistort_pinhole_image(image_path, params,input_dir)
                    # 获取原始文件名

                    filename = os.path.basename(image_path)
                    # 构建输出文件路径
                    output_path = os.path.join(output_dir, f'{filename}')
                    # 保存处理后的图片
                    cv2.imwrite(output_path, cropped_img)
                    print(f"已处理: {image_path}")


                except Exception as e:
                    print(f"处理图像 {image_path} 时出错: {str(e)}")
            print(f"所有图像已处理完成并保存到 {output_dir} 目录")
        except Exception as e:
            print(f"处理图像时出错: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="图像去畸变以及保存内参外参配置文件")
    parser.add_argument('--path', type=str, required=True, help='场景路径，例如 scene_1')
    args = parser.parse_args()
    scene_dir = args.path
    param_files = ["utils/Parameters/pinhole-front.txt","utils/Parameters/fisheye-front.txt", 
                   "utils/Parameters/fisheye-left.txt", "utils/Parameters/fisheye-right.txt", "utils/Parameters/pinhole-back.txt"]
    input_dirs = [f"{scene_dir}/CAM_FRONT_8M",f"{scene_dir}/CAM_FRONT_3M",
                   f"{scene_dir}/CAM_LEFT_3M", f"{scene_dir}/CAM_RIGHT_3M", 
                  f"{scene_dir}/CAM_BACK_3MH" ]
    output_dirs = [f"{scene_dir}/camera_image_0", f"{scene_dir}/camera_image_1", f"{scene_dir}/camera_image_2",
                   f"{scene_dir}/camera_image_3", f"{scene_dir}/camera_image_4"]
    
    for param_file, input_dir, output_dir in zip(param_files, input_dirs, output_dirs):
        # 创建输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        if input_dir==f"{scene_dir}/CAM_BACK_3MH" or input_dir==f"{scene_dir}/CAM_FRONT_8M":
            process_pinhole_image(param_file, input_dir, output_dir)
        else:
            process_fisheye_camera(param_file, input_dir, output_dir)

    camera_config_path = "utils/camera_config.json"
    update_camera_config(camera_config_path, param_files, input_dirs)
    generate_camera_config_dir(camera_config_path)
    
    print("\n处理完所有图片")
