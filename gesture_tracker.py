import cv2
import mediapipe as mp
import numpy as np
import math
from collections import deque

class GestureTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.frame_count = 0
        
        # Motion history for smoothing
        self.left_hand_history = deque(maxlen=5)
        self.right_hand_history = deque(maxlen=5)
        
        # Rotation tracking
        self.left_hand_angle = None
        self.right_hand_angle = None
        self.rotation_threshold = 15
        
        # Gesture cooldown
        self.last_gesture_time = {}
        self.cooldown = 0.3
        
        # Motion thresholds
        self.motion_threshold = 0.02
        
    def get_hand_angle(self, landmarks):
        """Calculate angle between wrist and index finger base"""
        wrist = landmarks[0]
        index_base = landmarks[5]
        
        dx = index_base.x - wrist.x
        dy = index_base.y - wrist.y
        
        angle = math.degrees(math.atan2(dy, dx))
        return angle
    
    def detect_rotation(self, current_angle, previous_angle, hand_label):
        """Detect significant rotation change"""
        if previous_angle is None:
            return None
        
        angle_diff = current_angle - previous_angle
        
        # Normalize angle difference to -180 to 180
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360
        
        if abs(angle_diff) > self.rotation_threshold:
            if angle_diff > 0:
                return f"rotate_{hand_label}_cw"
            else:
                return f"rotate_{hand_label}_ccw"
        
        return None
    
    def smooth_position(self, position, history):
        """Apply moving average to reduce jitter"""
        history.append(position)
        if len(history) < 2:
            return position
        
        avg_x = sum(p[0] for p in history) / len(history)
        avg_y = sum(p[1] for p in history) / len(history)
        return (avg_x, avg_y)
    
    def detect_motion(self, current_pos, previous_pos, hand_label):
        """Detect directional motion"""
        if previous_pos is None:
            return None
        
        dx = current_pos[0] - previous_pos[0]
        dy = current_pos[1] - previous_pos[1]
        
        gestures = []
        
        # Vertical motion
        if abs(dy) > self.motion_threshold:
            if dy < 0:  # Moving up (y decreases)
                gestures.append(f"increase_{hand_label}_up")
            else:  # Moving down
                gestures.append(f"decrease_{hand_label}_down")
        
        # Horizontal motion
        if abs(dx) > self.motion_threshold:
            if dx > 0:  # Moving right
                gestures.append(f"increase_{hand_label}_right")
            else:  # Moving left
                gestures.append(f"decrease_{hand_label}_left")
        
        return gestures if gestures else None
    
    def map_gesture_to_action(self, gesture, hand_label):
        """Map detected gesture to audio action"""
        actions = []
        
        if hand_label == "left":
            if "up" in gesture:
                actions.append("increase_bass")
            elif "down" in gesture:
                actions.append("decrease_bass")
            elif "right" in gesture:
                actions.append("increase_treble")
            elif "left" in gesture:
                actions.append("decrease_treble")
        
        elif hand_label == "right":
            if "up" in gesture:
                actions.append("increase_volume")
            elif "down" in gesture:
                actions.append("decrease_volume")
            elif "right" in gesture:
                actions.append("increase_speech")
            elif "left" in gesture:
                actions.append("decrease_speech")
        
        return actions
    
    def process_frame(self, frame):
        """Process a frame and detect gestures"""
        import time
        
        self.frame_count += 1
        
        # Convert BGR to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process with MediaPipe
        results = self.hands.process(frame_rgb)
        
        actions = []
        
        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                # Draw landmarks
                self.mp_draw.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                )
                
                # Get hand label
                hand_label = handedness.classification[0].label.lower()
                
                # Get wrist position
                wrist = hand_landmarks.landmark[0]
                current_pos = (wrist.x, wrist.y)
                
                # Smooth position
                if hand_label == "left":
                    smoothed_pos = self.smooth_position(current_pos, self.left_hand_history)
                    previous_pos = self.left_hand_history[-2] if len(self.left_hand_history) >= 2 else None
                else:
                    smoothed_pos = self.smooth_position(current_pos, self.right_hand_history)
                    previous_pos = self.right_hand_history[-2] if len(self.right_hand_history) >= 2 else None
                
                # Detect motion
                motion_gestures = self.detect_motion(smoothed_pos, previous_pos, hand_label)
                
                if motion_gestures:
                    for gesture in motion_gestures:
                        current_time = time.time()
                        if gesture not in self.last_gesture_time or \
                           current_time - self.last_gesture_time[gesture] > self.cooldown:
                            actions.extend(self.map_gesture_to_action(gesture, hand_label))
                            self.last_gesture_time[gesture] = current_time
                
                # Detect rotation
                current_angle = self.get_hand_angle(hand_landmarks.landmark)
                
                if hand_label == "left":
                    rotation = self.detect_rotation(current_angle, self.left_hand_angle, hand_label)
                    self.left_hand_angle = current_angle
                    
                    if rotation:
                        current_time = time.time()
                        if rotation not in self.last_gesture_time or \
                           current_time - self.last_gesture_time[rotation] > self.cooldown:
                            actions.append("toggle_echo")
                            self.last_gesture_time[rotation] = current_time
                else:
                    rotation = self.detect_rotation(current_angle, self.right_hand_angle, hand_label)
                    self.right_hand_angle = current_angle
                    
                    if rotation:
                        current_time = time.time()
                        if rotation not in self.last_gesture_time or \
                           current_time - self.last_gesture_time[rotation] > self.cooldown:
                            actions.append("toggle_reverb")
                            self.last_gesture_time[rotation] = current_time
                
                # Display hand label
                cv2.putText(frame, f"{hand_label.upper()}", 
                           (int(wrist.x * frame.shape[1]), int(wrist.y * frame.shape[0]) - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return frame, actions
    
    def release(self):
        """Release resources"""
        self.hands.close()
