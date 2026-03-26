# 实验二：ROS调试与可视化工具实验

## 一、实验目的与要求

| 实验编号 | 任务描述 |
|---|---|
| 5.1 | 使用 C++ 实现一个 LOG 节点，输出五个级别的日志，并通过 `rqt_console` 查看 |
| 5.3 | 使用 rqt 工具调试机器人信息（摄像头图像 + 坐标变换树） |

---

## 二、实验原理

### ROS 日志级别（从低到高）

| 级别 | C++ 宏 | 说明 |
|---|---|---|
| DEBUG | `ROS_DEBUG(...)` | 调试信息，默认不显示，需提升日志等级 |
| INFO  | `ROS_INFO(...)`  | 一般信息 |
| WARN  | `ROS_WARN(...)`  | 警告，潜在问题 |
| ERROR | `ROS_ERROR(...)` | 错误，需修复 |
| FATAL | `ROS_FATAL(...)` | 致命错误 |

### rqt 工具集（本实验涉及）

| 工具 | 用途 | 启动命令 |
|---|---|---|
| `rqt_console` | 查看/筛选 ROS 日志 | `rqt_console` |
| `rqt_image_view` | 查看摄像头图像话题 | `rqt_image_view` |
| `rqt_tf_tree` | 可视化坐标变换树 | `rosrun rqt_tf_tree rqt_tf_tree` |
| `rqt_graph` | 查看节点话题关系图 | `rqt_graph` |

---

## 三、工程文件结构

```
dhy_class_3/
├── LAB2_LOG_DEBUG_GUIDE.md          ← 本文档
├── LAUNCH_GUIDE.md                  ← 实验一文档（参数实验）
└── src/
    └── dhy_class_pkg/
        ├── CMakeLists.txt
        ├── package.xml
        ├── cfg/
        │   └── Tutorials.cfg        ← 动态参数配置（实验一）
        └── src/
            ├── dhy_ros_log.cpp      ← 【本实验 5.1】LOG节点
            ├── ros_debug_sim.cpp    ← 【本实验 5.3】仿真节点（PC专用）
            ├── ros_param.cpp        ← 实验一 参数节点
            └── ros_dynamic_speed.cpp← 实验一 动态速度节点
```

---

## 四、编译方法

```bash
cd ~/ROS_class_prj/dhy_class_3
source /opt/ros/noetic/setup.bash
catkin_make
```

编译成功后生成的可执行文件：

```
devel/lib/dhy_class_pkg/dhy_ros_log        ← 5.1 LOG节点
devel/lib/dhy_class_pkg/ros_debug_sim      ← 5.3 仿真节点
devel/lib/dhy_class_pkg/ros_param          ← 实验一
devel/lib/dhy_class_pkg/ros_dynamic_speed_node ← 实验一
```

---

## 五、启动指令

每个终端启动前，先 source 工作空间：
```bash
source ~/ROS_class_prj/dhy_class_3/devel/setup.bash
```

---

### 5.1 — C++ LOG 节点 + rqt_console

**总计需要 3 个终端：**

```bash
# 终端 1：启动 ROS Master
roscore

# 终端 2：运行 LOG 节点（每秒打印5条日志）
source ~/ROS_class_prj/dhy_class_3/devel/setup.bash
rosrun dhy_class_pkg dhy_ros_log

# 终端 3：打开日志查看工具
rqt_console
```

**rqt_console 操作说明：**
- 顶部下拉框可按日志级别筛选（Debug / Info / Warn / Error / Fatal）
- 可点击 Pause 暂停滚动，方便查看单条日志
- 可点击 Clear 清除历史日志
- DEBUG 消息已在代码中通过 `set_logger_level` 开启，无需手动设置

**预期输出（终端2）：**
```
[INFO]  LOG node started. Publishing all 5 log levels at 1 Hz.
[DEBUG] This is a DEBUG message. [count=0]
[INFO]  This is an INFO message. [count=0]
[WARN]  This is a WARNING message. [count=0]
[ERROR] This is an ERROR message. [count=0]
[FATAL] This is a FATAL message. [count=0]
...（每秒循环一次）
```

---

### 5.3 — 使用 rqt 工具调试机器人信息（PC 仿真版）

> **注意：** 工作机版本使用 `roslaunch upros_bringup bringup_w2a.launch` 启动真实硬件。
> 个人电脑上用 `ros_debug_sim` 节点模拟摄像头数据和坐标变换树，效果等价。

**总计需要 4 个终端：**

```bash
# 终端 1：启动 ROS Master
roscore

# 终端 2：启动仿真节点（发布虚拟摄像头图像 + TF 坐标树）
source ~/ROS_class_prj/dhy_class_3/devel/setup.bash
rosrun dhy_class_pkg ros_debug_sim

# 终端 3：查看摄像头图像
rqt_image_view
# → 在界面左上角下拉框中选择话题：/camera/color/image_raw
# → 应看到一张蓝绿渐变的彩色图像（320x240）

# 终端 4：查看坐标变换树
rosrun rqt_tf_tree rqt_tf_tree
# → 应看到三帧结构：world → base_link → camera_link
```

**ros_debug_sim 节点发布的内容：**

| 类型 | 话题/帧 | 说明 |
|---|---|---|
| `sensor_msgs/Image` | `/camera/color/image_raw` | 320×240 RGB渐变图，模拟摄像头 |
| TF 变换 | `world → base_link` | 机器人基座（原点） |
| TF 变换 | `base_link → camera_link` | 摄像头安装位置（前15cm，上10cm） |

---

## 六、与工作机运行的核心区别

| 对比项 | 工作机（实验室）| 个人电脑（本工作空间）|
|---|---|---|
| 启动硬件 | `roslaunch upros_bringup bringup_w2a.launch` | ❌ 无此功能包，用 `ros_debug_sim` 替代 |
| 摄像头图像来源 | 真实摄像头（Intel RealSense 等） | `ros_debug_sim` 发布的合成图像 |
| TF 坐标树来源 | 机器人 URDF + 驱动自动发布 | `ros_debug_sim` 手动广播3帧 |
| 话题 `/camera/color/image_raw` | 真实图像数据 | 渐变色合成图（可用于验证 rqt_image_view） |
| 5.4 激光雷达（/scan） | 真实数据 | 无（需实机验证）|
| 5.5 IMU（/imu/data） | 真实数据 | 无（需实机验证）|
| 5.1 LOG节点 | **完全相同，无区别** | **完全相同，无区别** |

---

## 七、迁移到工作机注意事项

### 步骤 1：打包工作空间

```bash
# 在个人电脑上执行
cd ~/ROS_class_prj
tar -czf dhy_class_3_backup.tar.gz dhy_class_3/src dhy_class_3/LAUNCH_GUIDE.md dhy_class_3/LAB2_LOG_DEBUG_GUIDE.md
```

### 步骤 2：传输到工作机

```bash
# 查询工作机 IP（在工作机终端执行）
ifconfig | grep "inet "

# 从个人电脑 SCP 传输
scp dhy_class_3_backup.tar.gz 工作机用户名@工作机IP:~/
```

### 步骤 3：在工作机上解压并编译

```bash
# 在工作机上执行
cd ~
tar -xzf dhy_class_3_backup.tar.gz
cd ~/dhy_class_3
source /opt/ros/noetic/setup.bash
catkin_make
```

### 步骤 4：在工作机上运行 5.3（真实硬件）

```bash
# 终端 1：启动机器人硬件
roslaunch upros_bringup bringup_w2a.launch

# 终端 2：查看摄像头图像（无需 ros_debug_sim）
rqt_image_view
# → 选择 /camera/color/image_raw → 看到真实摄像头画面

# 终端 3：查看坐标变换树
rosrun rqt_tf_tree rqt_tf_tree
# → 看到完整机器人 TF 树（比个人电脑版本帧数更多）
```

> `ros_debug_sim` 节点在工作机上**不需要运行**，真实硬件会自动发布这些话题。

### 工作机可能涉及的话题

```bash
# 启动硬件后，查看所有话题
rostopic list

# 查看摄像头相关话题
rostopic list | grep camera

# 查看 TF 帧列表
rosrun tf tf_echo world base_link
```

---

## 八、实验报告参考（问答）

1. **ROS 日志的作用**：在机器人程序调试和运行监控中，日志提供非侵入式的状态输出，不中断程序执行，便于问题定位。

2. **日志级别划分**：DEBUG < INFO < WARN < ERROR < FATAL，默认显示 INFO 及以上；可通过 `rqt_logger_level` 或代码中 `set_logger_level` 动态调整。

3. **配置输出不同级别**：通过 `ros::console::set_logger_level` 设置最低可见级别；也可在 `~/.ros/config/rosconsole.config` 文件中静态配置。

4. **宏使用示例**：
   ```cpp
   ROS_INFO("Speed: %.2f m/s", speed);
   ROS_WARN("Battery low: %d%%", battery);
   ROS_ERROR("Sensor disconnected: %s", sensor_name.c_str());
   ```
