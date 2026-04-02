#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机械臂键盘控制节点
框架参考: zx_teleop.py (upros_sim/src/zx_description/scripts/zx_teleop.py)
控制逻辑: 增量步进，每次按键让目标关节角度增减 step_size rad
"""

import rospy
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from std_msgs.msg import Float64
import sys, select, termios, tty

msg = """
机械臂键盘控制
---------------------------
关节控制（每次步进 0.1 rad）：
   q / a  :  joint_1  +/-
   w / s  :  joint_2  +/-
   e / d  :  joint_3  +/-
   r / f  :  joint_4  +/-
   t / g  :  joint_5  +/-
   y / h  :  爪子 开/合（同步）

空格键   :  全部关节归零

CTRL-C 退出
"""

# 关节名称与限位
JOINT_NAMES   = ['joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_5']
JOINT_LIMITS  = [(-1.8, 1.8)] * 5          # [lower, upper] rad

CLAW_LIMIT    = (-1.5, 1.5)
STEP          = 0.1                         # 每次按键步进量 (rad)

# 键位 -> (关节索引, 方向)   关节索引 0~4 对应 joint_1~5，5/6 对应 claw
keyBindings = {
    'q': (0,  1), 'a': (0, -1),
    'w': (1,  1), 's': (1, -1),
    'e': (2,  1), 'd': (2, -1),
    'r': (3,  1), 'f': (3, -1),
    't': (4,  1), 'g': (4, -1),
    'y': (5,  1), 'h': (5, -1),   # claw 开合
}


def getKey():
    """非阻塞读取一个按键，与 zx_teleop.py 保持一致"""
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def clamp(val, lo, hi):
    return max(lo, min(hi, val))


def publish_arm(pub_arm, joint_positions):
    """发布 JointTrajectory 到 arm_joint_controller"""
    traj = JointTrajectory()
    traj.joint_names = JOINT_NAMES
    point = JointTrajectoryPoint()
    point.positions = joint_positions[:]
    point.time_from_start = rospy.Duration(0.1)
    traj.points = [point]
    pub_arm.publish(traj)


def publish_claw(pub_claw1, pub_claw2, claw_pos):
    """发布 Float64 到两个爪子控制器"""
    pub_claw1.publish(Float64(claw_pos))
    pub_claw2.publish(Float64(-claw_pos))   # 两爪镜像对称


if __name__ == '__main__':
    settings = termios.tcgetattr(sys.stdin)

    rospy.init_node('arm_keyboard_ctrl')

    pub_arm   = rospy.Publisher('/arm_joint_controller/command',
                                JointTrajectory, queue_size=5)
    pub_claw1 = rospy.Publisher('/claw_joint_1_controller/command',
                                Float64, queue_size=5)
    pub_claw2 = rospy.Publisher('/claw_joint_2_controller/command',
                                Float64, queue_size=5)

    # 当前目标角度
    joint_pos = [0.0] * 5
    claw_pos  = 0.0

    count = 0   # 无键帧计数（与 zx_teleop.py 保持一致）

    try:
        print(msg)
        while not rospy.is_shutdown():
            key = getKey()

            if key in keyBindings:
                idx, direction = keyBindings[key]
                count = 0
                if idx < 5:
                    joint_pos[idx] = clamp(
                        joint_pos[idx] + direction * STEP,
                        JOINT_LIMITS[idx][0],
                        JOINT_LIMITS[idx][1]
                    )
                else:  # claw
                    claw_pos = clamp(
                        claw_pos + direction * STEP,
                        CLAW_LIMIT[0],
                        CLAW_LIMIT[1]
                    )
            elif key == ' ':
                # 全部归零
                joint_pos = [0.0] * 5
                claw_pos  = 0.0
                count = 0
                print("所有关节归零")
            else:
                count += 1
                if key == '\x03':   # CTRL-C
                    break

            publish_arm(pub_arm, joint_pos)
            publish_claw(pub_claw1, pub_claw2, claw_pos)

            if count == 1:
                # 打印当前关节角度
                pos_str = '  '.join(
                    [f'j{i+1}:{joint_pos[i]:.2f}' for i in range(5)]
                )
                print(f"  {pos_str}  claw:{claw_pos:.2f}")

    except Exception as e:
        print(e)

    finally:
        # 退出时归零
        publish_arm(pub_arm, [0.0] * 5)
        publish_claw(pub_claw1, pub_claw2, 0.0)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
