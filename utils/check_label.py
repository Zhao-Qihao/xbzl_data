import os
import numpy as np
from collections import defaultdict
import argparse

# 自定义数据集的类别
class_names = ['car', 'truck', 'bus', 'bicycle', 'pedestrian', 'traffic_cone', 'barrier']


def check_label_file(file_path, class_counts):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    for line_idx, line in enumerate(lines):
        parts = line.strip().split()
        if len(parts) != 8:
            print(f"[ERROR] {file_path} 第 {line_idx+1} 行: 数据长度不为 8，实际为 {len(parts)}")
            continue

        try:
            # 前7个是浮点数
            values = [float(p) for p in parts[:7]]
            label = parts[7]
            class_counts[label] += 1

            # 检查是否有 NaN 或 Inf
            if any(np.isnan(values)) or any(np.isinf(values)):
                print(f"[ERROR] {file_path} 第 {line_idx+1} 行: 包含 NaN 或 Inf")

            # 检查值是否过大（例如超出点云范围）
            if any(abs(v) > 100 for v in values):
                print(f"[WARNING] {file_path} 第 {line_idx+1} 行: 存在较大数值: {values}")

            # 检查类别是否存在
            if label not in class_names:
                print(f"[ERROR] {file_path} 第 {line_idx+1} 行: 类别 '{label}' 不在允许的类别列表中")

        except ValueError as e:
            print(f"[ERROR] {file_path} 第 {line_idx+1} 行: 数值转换失败 - {e}")

def save_statistics(total_frames, class_counts, scene_dir):
    stat_file = os.path.join(scene_dir, 'statistics.txt')
    with open(stat_file, 'w') as f:
        f.write(f"总帧数: {total_frames}\n")
        f.write("类别分布:\n")

        for class_name, count in class_counts.items():
            f.write(f"{class_name}: {count}\n")

    # 同时打印到控制台
    print(f"\n总处理帧数: {total_frames}")
    print("类别分布:")
    for class_name, count in class_counts.items():
        print(f"{class_name}: {count}")
    

def main():
    parser = argparse.ArgumentParser(description="检查标注文件并统计类别分布")
    parser.add_argument('--path', type=str, required=True, help='场景路径，例如 scene_1')
    args = parser.parse_args()
    scene_dir = args.path
    label_dir = os.path.join(scene_dir, 'labels')
    print(f"开始检查{args.path}下的标注文件...\n")
    total_frames = len([f for f in os.listdir(label_dir) if f.endswith('.txt')])  # 统计总帧数
    class_counts = defaultdict(int)                                              # 统计每个类别出现的次数
    for filename in os.listdir(label_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(label_dir, filename)
            check_label_file(file_path, class_counts)

    print("\n检查完成。")
    save_statistics(total_frames, class_counts, scene_dir)

if __name__ == '__main__':
    main()