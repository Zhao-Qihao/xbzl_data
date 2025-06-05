import open3d as o3d
import numpy as np
import json
import os
import numpy as np
import argparse

# 加载外参矩阵
with open("utils/lidar2m128.json", "r") as f:
    transforms = json.load(f)

def apply_transform(pcd, matrix):
    pcd.transform(np.array(matrix))
    return pcd

def transform2lidar32(pcd, matrix):
    matrix = np.linalg.inv(np.array(matrix))
    pcd.transform(matrix)
    return pcd

def save_point_cloud_to_bin(point_cloud, file_path):
    points = np.asarray(point_cloud.points, dtype=np.float32)
    points.tofile(file_path)
    print(f"已保存 .bin 文件：{file_path}")

def merge_all_lidars(timestamp, scene_dir):
    merged_pcd = o3d.geometry.PointCloud()
    source = [os.path.join(scene_dir, "LIDAR_FRONT"), os.path.join(scene_dir, "LIDAR_TOP_32"),
               os.path.join(scene_dir, "LIDAR_TOP_128")]
    for lidar_name in ["LIDAR_FRONT", "LIDAR_TOP_32", "LIDAR_TOP_128"]:
        pcd_path = f"{scene_dir}/{lidar_name}/{timestamp}.pcd"
        if os.path.exists(pcd_path):
            pcd = o3d.io.read_point_cloud(pcd_path)
            # 只有非主雷达才需要变换
            if lidar_name != "LIDAR_TOP_128":
                pcd = apply_transform(pcd, transforms[lidar_name])
            merged_pcd += pcd
    merged_pcd_32 = transform2lidar32(merged_pcd, transforms["LIDAR_TOP_32"])

    # 保存为 bin 文件，不保存 pcd
    save_point_cloud_to_bin(merged_pcd_32, f"{scene_dir}/lidar_point_cloud_1/{timestamp}.bin")

def main():
    parser = argparse.ArgumentParser(description="合并32线和前激光雷达点云")
    parser.add_argument('--path', type=str, required=True, help='场景路径，例如 scene_1')
    args = parser.parse_args()
    scene_dir = args.path
    os.makedirs(os.path.join(scene_dir, "lidar_point_cloud_1"), exist_ok=True)
    # 遍历所有时间戳
    timestamps = [str(int(f.split('.')[0])) for f in os.listdir(os.path.join(scene_dir, "LIDAR_TOP_32"))]
    for ts in timestamps:
        merge_all_lidars(ts, scene_dir)

if __name__ == '__main__':
    main()