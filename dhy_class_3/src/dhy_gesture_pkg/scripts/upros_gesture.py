#!/usr/bin/env python3

import cv2
import mediapipe as mp
import math

class UP_Gesture:
    def __init__(self):
        self.draw = mp.solutions.drawing_utils
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.75,
            min_tracking_confidence=0.75
        )

    def findHind(self, img):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        handlmsstyle = self.draw.DrawingSpec(color=(0, 0, 255), thickness=5)
        handconstyle = self.draw.DrawingSpec(color=(0, 255, 0), thickness=5)
        results = self.hands.process(imgRGB)
        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                self.draw.draw_landmarks(img, handLms, mp.solutions.hands.HAND_CONNECTIONS, handlmsstyle, handconstyle)
        return results.multi_hand_landmarks

    def detectNumber(self, hand_landmarks, img):
        h, w, _ = img.shape
        hand_landmark = hand_landmarks[0].landmark

        thumb_tip_id = 4
        index_finger_tip_id = 8
        middle_finger_tip_id = 12
        ring_finger_tip_id = 16
        pinky_finger_tip_id = 20
        pinky_finger_mcp_id = 17
        wrist_id = 0

        thumb_tip_y = hand_landmark[thumb_tip_id].y * h
        index_tip_y = hand_landmark[index_finger_tip_id].y * h
        middle_tip_y = hand_landmark[middle_finger_tip_id].y * h
        ring_tip_y = hand_landmark[ring_finger_tip_id].y * h
        pinky_tip_y = hand_landmark[pinky_finger_tip_id].y * h
        pinky_mcp_y = hand_landmark[pinky_finger_mcp_id].y * h
        wrist_y = hand_landmark[wrist_id].y * h

        thumb_tip_x = hand_landmark[thumb_tip_id].x * w
        index_tip_x = hand_landmark[index_finger_tip_id].x * w
        middle_tip_x = hand_landmark[middle_finger_tip_id].x * w
        ring_tip_x = hand_landmark[ring_finger_tip_id].x * w
        pinky_tip_x = hand_landmark[pinky_finger_tip_id].x * w
        pinky_mcp_x = hand_landmark[pinky_finger_mcp_id].x * w
        wrist_x = hand_landmark[wrist_id].x * w

        dist_thumb2wrist = math.sqrt((thumb_tip_x - wrist_x)**2 + (thumb_tip_y - wrist_y)**2)
        dist_index2wrist = math.sqrt((index_tip_x - wrist_x)**2 + (index_tip_y - wrist_y)**2)
        dist_middle2wrist = math.sqrt((middle_tip_x - wrist_x)**2 + (middle_tip_y - wrist_y)**2)
        dist_ring2wrist = math.sqrt((ring_tip_x - wrist_x)**2 + (ring_tip_y - wrist_y)**2)
        dist_pinky2wrist = math.sqrt((pinky_tip_x - wrist_x)**2 + (pinky_tip_y - wrist_y)**2)
        dist_pinky_mcp2wrist = math.sqrt((thumb_tip_x - pinky_mcp_x)**2 + (thumb_tip_y - pinky_mcp_y)**2)

        dist_index2wrist_ratio = dist_index2wrist / dist_thumb2wrist
        dist_middle2wrist_ratio = dist_middle2wrist / dist_thumb2wrist
        dist_ring2wrist_ratio = dist_ring2wrist / dist_thumb2wrist
        dist_pinky2wrist_ratio = dist_pinky2wrist / dist_thumb2wrist
        dist_pinky_mcp2wrist_ratio = dist_pinky_mcp2wrist / dist_thumb2wrist

        # 0: fist
        if (dist_index2wrist_ratio < 1.9 and dist_middle2wrist_ratio < 1.8 and
                dist_ring2wrist_ratio < 1.6 and dist_pinky2wrist_ratio < 1.4 and
                dist_pinky_mcp2wrist_ratio < 0.8):
            return 0
        # 1: index finger up
        elif (2.0 < dist_index2wrist_ratio and dist_middle2wrist_ratio < 1.8 and
              dist_ring2wrist_ratio < 1.6 and dist_pinky2wrist_ratio < 1.4 and
              dist_pinky_mcp2wrist_ratio < 0.8):
            return 1
        # 2: index + middle up
        elif (2.0 < dist_index2wrist_ratio and 1.9 < dist_middle2wrist_ratio and
              dist_ring2wrist_ratio < 1.6 and dist_pinky2wrist_ratio < 1.4 and
              dist_pinky_mcp2wrist_ratio < 0.8):
            return 2
        # 3: index + middle + ring up
        elif (2.0 < dist_index2wrist_ratio and 1.9 < dist_middle2wrist_ratio and
              1.75 < dist_ring2wrist_ratio and dist_pinky2wrist_ratio < 1.4 and
              dist_pinky_mcp2wrist_ratio < 0.8):
            return 3
        # 4: four fingers up
        elif (2.0 < dist_index2wrist_ratio and 1.9 < dist_middle2wrist_ratio and
              1.75 < dist_ring2wrist_ratio and 1.5 < dist_pinky2wrist_ratio and
              dist_pinky_mcp2wrist_ratio < 0.8):
            return 4
        # 5: open hand
        elif (dist_index2wrist_ratio > 0.5 and dist_middle2wrist_ratio > 0.5 and
              dist_ring2wrist_ratio > 0.5 and 0.9 < dist_pinky_mcp2wrist_ratio < 1.2):
            return 5
        # 6: three fingers close
        elif (dist_index2wrist_ratio < 0.5 and dist_middle2wrist_ratio < 0.5 and
              dist_ring2wrist_ratio < 0.5):
            return 6
        else:
            return -1
