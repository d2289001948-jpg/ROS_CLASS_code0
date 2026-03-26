# 实验四：参数与动态参数实验 — 完整流程文档

## 一、工程结构

```
dhy_class_3/
├── src/
│   └── dhy_class_pkg/
│       ├── CMakeLists.txt        ← 编译规则（已配置 dynamic_reconfigure）
│       ├── package.xml           ← 依赖声明（含 dynamic_reconfigure）
│       ├── cfg/
│       │   └── Tutorials.cfg     ← 动态参数定义文件
│       └── src/
│           ├── ros_param.cpp         ← 5.1 C++ 参数节点
│           └── ros_dynamic_speed.cpp ← 5.5 动态速度控制节点
├── devel/                        ← catkin_make 生成（含可执行文件）
├── build/                        ← catkin_make 生成（编译缓存）
└── LAUNCH_GUIDE.md               ← 本文档
```

---

## 二、整体开发流程回顾

```
1. 编写 cfg/Tutorials.cfg
      ↓ 定义哪些参数可动态调整（类型、范围、默认值）
2. 修改 CMakeLists.txt
      ↓ 添加 dynamic_reconfigure 到 find_package
      ↓ 添加 generate_dynamic_reconfigure_options(cfg/Tutorials.cfg)
      ↓ 添加新节点的 add_executable / add_dependencies / target_link_libraries
3. 修改 package.xml
      ↓ 添加 dynamic_reconfigure 的 build_depend 和 exec_depend
4. 编写 src/ros_dynamic_speed.cpp
      ↓ 注册动态参数回调，在回调中更新速度变量
      ↓ 主循环以 10Hz 持续发布 /cmd_vel
5. catkin_make
      ↓ 自动生成 dhy_class_pkg/TutorialsConfig.h（供 C++ 代码使用）
      ↓ 编译生成可执行文件
```

---

## 三、编译方法

```bash
# 在工作空间根目录执行
cd ~/ROS_class_prj/dhy_class_3
catkin_make
```

编译成功后可执行文件位于：
- `devel/lib/dhy_class_pkg/ros_param`
- `devel/lib/dhy_class_pkg/ros_dynamic_speed_node`

---

## 四、启动指令

### 4.1 实验 5.1 — C++ 参数节点

```bash
# 终端 1
roscore

# 终端 2
source ~/ROS_class_prj/dhy_class_3/devel/setup.bash
rosrun dhy_class_pkg ros_param
```

**预期输出：**
```
[INFO] Private 1 The value of my_param is         ← 首次获取，为空
[INFO] Private 2 The value of my_param is hello   ← 私有参数设置后读取
[INFO] The value of my_param is hello              ← 全局参数设置后读取
```

**验证参数（节点运行时，新开终端）：**
```bash
rosparam list                          # 查看所有参数
rosparam get /my_param                 # 全局参数
rosparam get /my_param_node/my_param   # 私有参数
```

---

### 4.2 实验 5.5 — 动态配置机器人速度

#### 个人电脑验证（无真实机器人）

```bash
# 终端 1
roscore

# 终端 2 — 动态速度节点
source ~/ROS_class_prj/dhy_class_3/devel/setup.bash
rosrun dhy_class_pkg ros_dynamic_speed_node

# 终端 3 — 图形化参数调节界面
rosrun rqt_reconfigure rqt_reconfigure

# 终端 4（可选）— 观察话题输出
rostopic echo /cmd_vel
```

在 rqt_reconfigure 中拖动 **double_param** 滑块（-0.25 ~ 0.25），
终端 2 实时打印参数更新，`/cmd_vel` 同步变化。

#### 连接真实机器人（完整 5.5）

```bash
# 终端 1 — 启动机器人底盘驱动
roslaunch upros_bringup bringup_w2a.launch

# 终端 2 — 动态速度节点
source ~/ROS_class_prj/dhy_class_3/devel/setup.bash
rosrun dhy_class_pkg ros_dynamic_speed_node

# 终端 3 — 图形化参数调节界面
rosrun rqt_reconfigure rqt_reconfigure
```

---

## 五、动态参数说明（Tutorials.cfg）

| 参数 | 类型 | 范围 | 用途 |
|---|---|---|---|
| double_param | double | -0.25 ~ 0.25 | **机器人线速度 (m/s)** |
| int_param | int | 0 ~ 100 | 整数示例 |
| bool_param | bool | True / False | 布尔示例 |
| str_param | string | — | 字符串示例 |
| size | enum | Small(0) / Medium(1) / Large(2) / ExtraLarge(3) | 枚举示例 |

---

## 六、迁移到工作机注意事项

### 迁移方式

```bash
# 在个人电脑上打包（排除编译产物，只迁移源码）
cd ~/ROS_class_prj
tar --exclude=dhy_class_3/build \
    --exclude=dhy_class_3/devel \
    -czf dhy_class_3_src.tar.gz dhy_class_3/

# 传输到工作机（替换为实际 IP）
scp dhy_class_3_src.tar.gz user@robot_ip:~/ROS_class_prj/
```

### 工作机上解压并编译

```bash
cd ~/ROS_class_prj
tar -xzf dhy_class_3_src.tar.gz
cd dhy_class_3
catkin_make
```

### 迁移后需确认的事项

1. **机器人速度话题名称**
   - 当前代码发布到 `/cmd_vel`
   - 工作机启动后用以下命令确认真实机器人的话题名：
     ```bash
     roslaunch upros_bringup bringup_w2a.launch
     rostopic list | grep vel
     ```
   - 若话题名不同，修改 `ros_dynamic_speed.cpp` 第 22 行：
     ```cpp
     ros::Publisher cmd_pub = nh.advertise<geometry_msgs::Twist>("/cmd_vel", 10);
     //                                                            ↑ 改为实际话题名
     ```
   - 修改后重新 `catkin_make`

2. **ROS 环境依赖**
   - 确认工作机已安装：`ros-noetic-dynamic-reconfigure`
   - 检查命令：`rospack find dynamic_reconfigure`

3. **source 路径**
   - 若工作机用户名不同，`devel/setup.bash` 路径需对应调整

4. **git 工作流（按实验报告要求）**
   ```bash
   git checkout -b feature/week3-param    # 创建分支
   git add src/dhy_class_pkg/             # 只提交源码
   git commit -m "add dynamic speed control node (exp4 5.5)"
   git checkout master
   git merge feature/week3-param
   git push
   ```
