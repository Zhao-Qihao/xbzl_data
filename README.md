## 1 数据预处理
首先拿到以下格式的数据：
```
scene_4
├── CAM_BACK_3MH
├── CAM_FRONT_3M
├── CAM_FRONT_8M
├── CAM_LEFT_3M
├── CAM_RIGHT_3M
├── LIDAR_FRONT
├── LIDAR_LEFT
├── LIDAR_REAR
├── LIDAR_RIGHT
├── LIDAR_TOP_128
├── LIDAR_TOP_32
```
处理数据前先查看每个文件夹下的帧是否一致，若不一致则删除多余的帧。

然后将其放入总的data目录中，并进入到data目录。data目录如下所示：
```
data
├── scene_1
├── scene_2
├── scene_3
├── scene_4
├── scene_5
└── utils
    ├── 32m2cameras.json
    ├── camera_config.json
    ├── check_label.py
    ├── lidar2m128.json
    ├── merge_pcd.py
    ├── merge_top32_front.py
    ├── Parameters
    └── undistort.py
```
## 2 合并点云
```merge_pcd.py```是将各激光雷达数据转换合成到LIDAR_TOP_32激光雷达坐标系的脚本。(之所以转到32激光雷达坐标系是因为32激光雷达数据量是实际运行推理时所用的坐标系。)
首先使用以下命令生成所有lidar合成的pcd格式点云数据lidar_point_cloud_0，以及LIDAR_TOP_32和LIDAR_FRONT合成的bin格式点云数据lidar_point_cloud_1，此时都为LIDAR_TOP_32激光雷达坐标系
```
python utils/merge_pcd.py --path='scene_4'
python utils/merge_top32_front.py --path='scene_4'
```
生成lidar_point_cloud_0是为了更好的标注数据用(标注平台只接受pcd格式点云)，生成lidar_point_cloud_1是为了训练模型/测试模型使用(bin格式点云读取更快，所以在训练时候使用bin格式)。
## 3 图像去畸变
使用以下命令对图像进行去畸变，并生成内参camera_config文件夹
```
python utils/undistort.py --path='scene_4'
```
由此得到最终送入标注软件的数据目录：
```
scene_4
├── camera_config
├── camera_image_0
├── camera_image_1
├── camera_image_2
├── camera_image_3
├── camera_image_4
├── lidar_point_cloud_0
```
检查以上目录是否都存在于data目录下。最后再使用zip压缩命令将该场景数据目录打包
```
$ cd scene_4
$ zip -r scene_4.zip camera_config camera_image_0 camera_image_1 camera_image_2 camera_image_3 camera_image_4 lidar_point_cloud_0
```
压缩完成后即可提交数据scene_4.zip进标注软件。

## 4 标注
若是第一次使用标注工具，需要先配置标注工具：
```
wget https://github.com/xtreme1-io/xtreme1/releases/download/v0.9.1/xtreme1-v0.9.1.zip
unzip -d xtreme1-v0.9.1 xtreme1-v0.9.1.zip
cd xtreme1-v0.9.1
```
然后注意一下这里后续需要拉取docker镜像，但是原仓库中镜像cuda版本比较低了，30系列和40系列GPU已经不能运行，所以这里我上传了一个可以运行的镜像到docker hub中。

需要修改
docker-compose.yml中的第125行

```image: basicai/xtreme1-point-cloud-object-detection```，

将其改为

```image: zhaoqihao/xtreme1-point-cloud-object-detection```

然后使用
```
docker compose --profile model up
```
在终端启动标注工具。注意第一次运行时因为要拉取docker，需要耗费比较长的时间，后面再运行的时候进入就很快了。

再访问 [http://localhost:8190/](http://localhost:8190/) 进入。若是非本地运行的标注软件，请将localhost改为对应服务器的ip地址即可在本地访问。
具体标注功能可查看文档[BasicAI](https://docs.basic.ai/docs/basicai-cloud-introduction)

## 5 提取标注结果
标注完成后点击标注软件的export拿到标注结果文件夹，文件目录如下所示：
```
scene_4-timestamp
├── data
└── result
```
将scene_4-timestamp移动到scene_4目录下，再返回到总的data文件夹，运行extract_label.py即可提取标注结果到labels文件夹下。

```
python utils/extract_label.py --path='scene_4'
```
然后继续在scene目录下运行
```
python utils/check_label.py --path='scene_4'
```
以此检查标注结果，若终端未显示ERROR和WARNING，则说明标注结果无误。，同时scene目录下会生成statistics.txt文件，记录了该scene的帧数以及每个类别的数量信息。
由此得到了单个场景可标注的数据(请确保scene_1目录下存在下述文件和文件夹)：
```
scene_4
├── camera_config
├── camera_image_0
├── camera_image_1
├── camera_image_2
├── camera_image_3
├── camera_image_4
├── lidar_point_cloud_1
├── labels
├── statistics.txt
```
若要节约存储空间，除了上述之外的其他文件夹都可以删去。

以上只是处理了一个场景的数据，若要处理多个场景的数据，请重复以上步骤，并将以上所有命令中涉及scene_4的替换为你的场景名称，如scene_1，scene_2，scene_3等等。每个场景数据量为几百帧。

## 6 将标注好的数据加入到总的数据集中
将上述得到的scene_1数据移动到总的数据集data文件夹下。
最终data文件夹结构如下：
```
data
├── scene_1
├── scene_2
├── scene_3
├── scene_4
├── scene_5
├── utils
└── trainval.yaml
```
trainval.yaml文件为训练集和验证集的索引。文件内容如下：
```
train:
  - scene_1
  - scene_2
  - scene_3
val:
  - scene_4
```
若有新的场景数据加进来，请将场景数据放在data文件夹下，并修改trainval.yaml文件。注意train和val的数据比例控制在8:2或9:1左右。

## 7 训练模型
