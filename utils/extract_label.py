import os
import json
import argparse

def convert_annotations(input_dir, output_dir):
    # 创建输出目录（如果不存在）
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 遍历输入目录中的所有 JSON 文件
    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(input_dir, filename)
            label_file_path = os.path.join(output_dir, os.path.splitext(filename)[0] + '.txt')

            with open(file_path, 'r') as f:
                data = json.load(f)

            with open(label_file_path, 'w') as label_file:
                print(f"Processing file: {file_path}")
                for obj in data[0]['objects']:  # 遍历ground truth对象
                    center3D = obj['contour']['center3D']
                    size3D = obj['contour']['size3D']
                    class_name = obj['className']
                    yaw = obj['contour']['rotation3D']

                    # 提取坐标和尺寸
                    x = round(center3D['x'], 3)
                    y = round(center3D['y'], 3)
                    z = round(center3D['z'], 3)
                    dx = round(size3D['x'], 3)
                    dy = round(size3D['y'], 3)
                    dz = round(size3D['z'], 3)

                    yaw = round(yaw['z'], 3)

                    # 写入文件
                    label_file.write(f"{x} {y} {z} {dx} {dy} {dz} {yaw} {class_name}\n")
                # for obj in data[1]['objects']:  # 遍历model predictions对象
                #     center3D = obj['contour']['center3D']
                #     size3D = obj['contour']['size3D']
                #     class_name = obj['className']

                #     # 提取坐标和尺寸
                #     x = round(center3D['x'], 3)
                #     y = round(center3D['y'], 3)
                #     z = round(center3D['z'], 3)
                #     dx = round(size3D['x'], 3)
                #     dy = round(size3D['y'], 3)
                #     dz = round(size3D['z'], 3)

                #     # 写入文件
                #     label_file.write(f"{x} {y} {z} {dx} {dy} {dz} {class_name}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="提取标注信息")
    parser.add_argument('--path', type=str, required=True, help='场景路径，例如 scene_1')
    args = parser.parse_args()
    scene_dir = args.path
    timestamp_dir = [d for d in os.listdir(scene_dir) if d.startswith(scene_dir + '-')]
    input_dir = os.path.join(scene_dir, timestamp_dir[0], 'result')  # JSON 文件所在目录
    output_dir = os.path.join(scene_dir, 'labels')  # 输出标签文件目录
    convert_annotations(input_dir, output_dir)