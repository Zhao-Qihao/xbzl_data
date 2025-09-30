import open3d as o3d
import numpy as np
import json
import os
import argparse

# 加载外参矩阵
with open("utils/lidar2m32.json", "r") as f:
    transforms = json.load(f)

def apply_transform(pcd, matrix):
    pcd.transform(np.array(matrix))
    return pcd

def transform2lidar32(pcd, matrix):
    matrix = np.linalg.inv(np.array(matrix))
    pcd.transform(matrix)
    return pcd

def merge_all_lidars(timestamp, scene_dir):
    merged_pcd = o3d.geometry.PointCloud()
    for lidar_name in ["LIDAR_FRONT", "LIDAR_REAR", "LIDAR_TOP_32"]:
        pcd_path = f"{scene_dir}/{lidar_name}/{timestamp}.pcd"
        if os.path.exists(pcd_path):
            pcd = o3d.io.read_point_cloud(pcd_path)
            # 只有非主雷达才需要变换
            if lidar_name != "LIDAR_TOP_32":
                pcd = apply_transform(pcd, transforms[lidar_name])
                print(f"已应用变换矩阵到 {lidar_name}")
            merged_pcd += pcd

    # 保存合并后的点云
    o3d.io.write_point_cloud(f"{scene_dir}/lidar_point_cloud_0/{timestamp}.pcd", merged_pcd)
    print(f"已保存合并后的点云：{scene_dir}/lidar_point_cloud_0/{timestamp}.pcd")

def main():
    parser = argparse.ArgumentParser(description="合并所有点云")
    parser.add_argument('--path', type=str, required=True, help='场景路径，例如 scene_1')
    args = parser.parse_args()
    scene_dir = args.path
    os.makedirs(os.path.join(scene_dir, "lidar_point_cloud_0"), exist_ok=True)
    # 遍历所有时间戳
    timestamps = [str(int(f.split('.')[0])) for f in os.listdir(os.path.join(scene_dir, "LIDAR_TOP_32"))]
    for ts in timestamps:
        merge_all_lidars(ts, scene_dir)

if __name__ == '__main__':
    main()