"""
Gesture-Controlled Audio Mixer with Visual Jogwheels
Requirements:
pip install opencv-python mediapipe numpy scipy soundfile sounddevice

Usage:
1. Place your audio file in the same directory as this script
2. Update AUDIO_FILE path below
3. Run: python main.py
"""

import cv2
import sys
import os
import numpy as np
from gesture_tracker import GestureTracker
from audio_controller import AudioController

# Configuration
AUDIO_FILE = "song.mp3"  # Change this to your audio file path

# Jogwheel configuration
JOGWHEEL_RADIUS = 60
JOGWHEEL_ALPHA = 0.15  # Very low opacity for high transparency - can see hands clearly
JOGWHEEL_FADE_FRAMES = 30  # How long jogwheel stays visible after gesture

class JogwheelVisualizer:
    """Handles jogwheel visualization for audio parameters"""
    
    def __init__(self):
        self.active_wheels = {}  # {parameter_name: {'value': float, 'frames_left': int, 'position': (x, y)}}
        self.positions = {
            'bass': (120, 120),
            'treble': (120, 250),
            'speech': (520, 120),
            'volume': (520, 250),
            'echo': (320, 120),
            'reverb': (320, 250)
        }
    
    def update(self, parameter, value):
        """Update or activate a jogwheel for a parameter"""
        self.active_wheels[parameter] = {
            'value': value,
            'frames_left': JOGWHEEL_FADE_FRAMES,
            'position': self.positions.get(parameter, (320, 240))
        }
    
    def draw(self, frame):
        """Draw all active jogwheels on the frame"""
        overlay = frame.copy()
        
        # Update and draw each active wheel
        to_remove = []
        for param, data in self.active_wheels.items():
            # Decrease fade counter
            data['frames_left'] -= 1
            if data['frames_left'] <= 0:
                to_remove.append(param)
                continue
            
            # Calculate alpha based on fade
            fade_alpha = min(1.0, data['frames_left'] / JOGWHEEL_FADE_FRAMES)
            alpha = JOGWHEEL_ALPHA * fade_alpha
            
            # Draw jogwheel
            self._draw_jogwheel(overlay, data['position'], data['value'], param)
        
        # Remove expired wheels
        for param in to_remove:
            del self.active_wheels[param]
        
        # Blend overlay with original frame
        if self.active_wheels:
            cv2.addWeighted(overlay, JOGWHEEL_ALPHA, frame, 1 - JOGWHEEL_ALPHA, 0, frame)
        
        return frame
    
    def _draw_jogwheel(self, frame, position, value, parameter):
        """Draw a single jogwheel"""
        cx, cy = position
        radius = JOGWHEEL_RADIUS
        
        # Draw outer circle
        cv2.circle(frame, (cx, cy), radius, (100, 100, 100), 2)
        cv2.circle(frame, (cx, cy), radius - 5, (60, 60, 60), 1)
        
        # Draw center circle
        cv2.circle(frame, (cx, cy), 8, (200, 200, 200), -1)
        
        # Draw tick marks
        for i in range(12):
            angle = i * 30 * np.pi / 180
            x1 = int(cx + (radius - 10) * np.cos(angle))
            y1 = int(cy + (radius - 10) * np.sin(angle))
            x2 = int(cx + (radius - 3) * np.cos(angle))
            y2 = int(cy + (radius - 3) * np.sin(angle))
            cv2.line(frame, (x1, y1), (x2, y2), (150, 150, 150), 1)
        
        # Calculate needle angle based on value
        # Map value range to -135° to +135° (270° total range)
        if parameter in ['bass', 'treble', 'speech']:
            # Range -12 to +12
            angle_deg = (value / 12.0) * 135
        elif parameter == 'volume':
            # Range 0 to 2
            angle_deg = ((value - 1.0) / 1.0) * 135
        elif parameter in ['echo', 'reverb']:
            # Binary: OFF = -90°, ON = +90°
            angle_deg = 90 if value == "ON" else -90
        else:
            angle_deg = 0
        
        # Draw needle
        angle_rad = (angle_deg - 90) * np.pi / 180  # -90 to start from top
        needle_length = radius - 15
        needle_x = int(cx + needle_length * np.cos(angle_rad))
        needle_y = int(cy + needle_length * np.sin(angle_rad))
        
        # Draw needle with gradient effect
        cv2.line(frame, (cx, cy), (needle_x, needle_y), (0, 255, 255), 3)
        cv2.circle(frame, (needle_x, needle_y), 4, (0, 200, 255), -1)
        
        # Draw value text in CENTER of jogwheel
        if parameter in ['bass', 'treble', 'speech']:
            value_text = f"{value:+.1f}"
        elif parameter == 'volume':
            value_text = f"{value:.2f}"
        else:
            value_text = str(value)
        
        value_size = cv2.getTextSize(value_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        value_x = cx - value_size[0] // 2
        value_y = cy + value_size[1] // 2
        
        # Draw background for value text for better readability
        padding = 5
        cv2.rectangle(frame, 
                     (value_x - padding, value_y - value_size[1] - padding),
                     (value_x + value_size[0] + padding, value_y + padding),
                     (0, 0, 0), -1)
        
        cv2.putText(frame, value_text, (value_x, value_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Draw parameter label BELOW jogwheel
        label = parameter.upper()
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        label_x = cx - label_size[0] // 2
        label_y = cy + radius + 25
        
        # Draw background for label
        cv2.rectangle(frame,
                     (label_x - padding, label_y - label_size[1] - padding),
                     (label_x + label_size[0] + padding, label_y + padding),
                     (0, 0, 0), -1)
        
        cv2.putText(frame, label, (label_x, label_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)


def print_status(status):
    """Print current audio status to console"""
    print("\r" + " " * 100, end="")
    print(f"\rBass: {status['bass']:+.1f} | Treble: {status['treble']:+.1f} | "
          f"Speech: {status['speech']:+.1f} | Volume: {status['volume']:.2f} | "
          f"Echo: {status['echo']} | Reverb: {status['reverb']}", end="", flush=True)

def main():
    print("=" * 80)
    print("GESTURE-CONTROLLED AUDIO MIXER")
    print("=" * 80)
    
    # Check if audio file exists
    if not os.path.exists(AUDIO_FILE):
        print(f"⚠️  Audio file '{AUDIO_FILE}' not found!")
        print("💡 Running in DEMO MODE (no audio playback)")
        print("   Update the AUDIO_FILE path in main.py to enable audio")
        audio_controller = None
    else:
        print(f"✓ Loading audio: {AUDIO_FILE}")
        try:
            audio_controller = AudioController(AUDIO_FILE)
            audio_controller.start_playback()
            print("✓ Audio playback started!")
        except Exception as e:
            print(f"⚠️  Audio error: {e}")
            print("💡 Running in DEMO MODE (video only)")
            audio_controller = None
    
    # Initialize gesture tracker
    print("✓ Initializing gesture tracker...")
    try:
        gesture_tracker = GestureTracker()
    except Exception as e:
        print(f"❌ Error initializing gesture tracker: {e}")
        if audio_controller:
            audio_controller.stop_playback()
        sys.exit(1)
    
    # Initialize jogwheel visualizer
    jogwheel_viz = JogwheelVisualizer()
    print("✓ Jogwheel visualizer ready!")
    
    # Open webcam
    print("✓ Opening webcam...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Error: Could not open webcam!")
        if audio_controller:
            audio_controller.stop_playback()
        gesture_tracker.release()
        sys.exit(1)
    
    # Set camera properties for better performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    print("✓ Webcam ready!")
    print("\n" + "=" * 80)
    print("GESTURE CONTROLS:")
    print("=" * 80)
    print("LEFT HAND:  ↑=Bass+  ↓=Bass-  →=Treble+  ←=Treble-  Rotate=Echo Toggle")
    print("RIGHT HAND: ↑=Vol+   ↓=Vol-   →=Speech+  ←=Speech-  Rotate=Reverb Toggle")
    print("=" * 80)
    print("\n🎥 Camera window should appear now...")
    print("📌 Press 'q' to quit\n")
    
    # Create window
    window_name = 'Gesture-Controlled Audio Mixer'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("\n⚠️  Failed to read frame from camera")
                break
            
            frame_count += 1
            
            # Flip frame for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Process frame and detect gestures
            try:
                processed_frame, actions = gesture_tracker.process_frame(frame)
            except Exception as e:
                print(f"\n⚠️  Gesture tracking error: {e}")
                processed_frame = frame
                actions = []
            
            # Handle detected actions and update jogwheels
            if actions:
                for action in actions:
                    if audio_controller:
                        audio_controller.handle_action(action)
                    
                    # Update jogwheel for this action
                    # Parse action to determine which parameter changed
                    if 'bass' in action.lower():
                        param = 'bass'
                    elif 'treble' in action.lower():
                        param = 'treble'
                    elif 'speech' in action.lower():
                        param = 'speech'
                    elif 'volume' in action.lower():
                        param = 'volume'
                    elif 'echo' in action.lower():
                        param = 'echo'
                    elif 'reverb' in action.lower():
                        param = 'reverb'
                    else:
                        param = None
                    
                    if param:
                        # Get current value and update jogwheel
                        if audio_controller:
                            status = audio_controller.get_status()
                            jogwheel_viz.update(param, status[param])
            
            # Get status
            if audio_controller:
                status = audio_controller.get_status()
            else:
                status = {
                    "bass": 0.0,
                    "treble": 0.0,
                    "speech": 0.0,
                    "volume": 1.0,
                    "echo": "OFF",
                    "reverb": "OFF"
                }
            
            # Draw jogwheels on frame
            processed_frame = jogwheel_viz.draw(processed_frame)
            
            # Display status on frame (moved to right side to avoid jogwheel overlap)
            y_offset = 30
            x_offset = processed_frame.shape[1] - 200  # Right side
            cv2.putText(processed_frame, f"Bass: {status['bass']:+.1f}", (x_offset, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y_offset += 30
            cv2.putText(processed_frame, f"Treble: {status['treble']:+.1f}", (x_offset, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y_offset += 30
            cv2.putText(processed_frame, f"Speech: {status['speech']:+.1f}", (x_offset, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y_offset += 30
            cv2.putText(processed_frame, f"Volume: {status['volume']:.2f}", (x_offset, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y_offset += 30
            cv2.putText(processed_frame, f"Echo: {status['echo']}", (x_offset, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            y_offset += 30
            cv2.putText(processed_frame, f"Reverb: {status['reverb']}", (x_offset, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Add frame counter and mode indicator
            mode_text = "DEMO MODE" if not audio_controller else "LIVE AUDIO"
            cv2.putText(processed_frame, mode_text, (10, processed_frame.shape[0] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            
            # Print status to console (every 10 frames to reduce flicker)
            if frame_count % 10 == 0 and audio_controller:
                print_status(status)
            
            # Show frame
            cv2.imshow(window_name, processed_frame)
            
            # Check for quit (reduce wait time for more responsive display)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n\n👋 Quit command received")
                break
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        if audio_controller:
            audio_controller.stop_playback()
        gesture_tracker.release()
        cap.release()
        cv2.destroyAllWindows()
        print("✅ Done!")

if __name__ == "__main__":
    main()