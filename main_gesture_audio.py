"""
Gesture-Controlled Audio Mixer
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
from gesture_tracker import GestureTracker
from audio_controller import AudioController

# Configuration
AUDIO_FILE = "song.mp3"  # Change this to your audio file path

def print_status(status):
    """Print current audio status to console"""
    print("\r" + " " * 100, end="")
    print(f"\rBass: {status['bass']:+.1f} | Treble: {status['treble']:+.1f} | "
          f"Speech: {status['speech']:+.1f} | Volume: {status['volume']:.2f} | "
          f"Echo: {status['echo']} | Reverb: {status['reverb']}", end="", flush=True)

def main():
    # Check if audio file exists
    if not os.path.exists(AUDIO_FILE):
        print(f"Error: Audio file '{AUDIO_FILE}' not found!")
        print("Please update the AUDIO_FILE path in main.py")
        sys.exit(1)
    
    print("Initializing Gesture-Controlled Audio Mixer...")
    print(f"Loading audio: {AUDIO_FILE}")
    
    # Initialize components
    try:
        audio_controller = AudioController(AUDIO_FILE)
        gesture_tracker = GestureTracker()
    except Exception as e:
        print(f"Error initializing components: {e}")
        sys.exit(1)
    
    # Start audio playback
    audio_controller.start_playback()
    print("Audio playback started!")
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam!")
        audio_controller.stop_playback()
        sys.exit(1)
    
    print("\nGesture Control Active!")
    print("=" * 80)
    print("LEFT HAND:  ↑=Bass+  ↓=Bass-  →=Treble+  ←=Treble-  Rotate=Echo Toggle")
    print("RIGHT HAND: ↑=Vol+   ↓=Vol-   →=Speech+  ←=Speech-  Rotate=Reverb Toggle")
    print("=" * 80)
    print("\nPress 'q' to quit\n")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Flip frame for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Process frame and detect gestures
            processed_frame, actions = gesture_tracker.process_frame(frame)
            
            # Handle detected actions
            if actions:
                for action in actions:
                    audio_controller.handle_action(action)
            
            # Display status on frame
            status = audio_controller.get_status()
            y_offset = 30
            cv2.putText(processed_frame, f"Bass: {status['bass']:+.1f}", (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y_offset += 30
            cv2.putText(processed_frame, f"Treble: {status['treble']:+.1f}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y_offset += 30
            cv2.putText(processed_frame, f"Speech: {status['speech']:+.1f}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y_offset += 30
            cv2.putText(processed_frame, f"Volume: {status['volume']:.2f}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y_offset += 30
            cv2.putText(processed_frame, f"Echo: {status['echo']}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            y_offset += 30
            cv2.putText(processed_frame, f"Reverb: {status['reverb']}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Print status to console
            print_status(status)
            
            # Show frame
            cv2.imshow('Gesture-Controlled Audio Mixer', processed_frame)
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    
    finally:
        # Cleanup
        print("\n\nCleaning up...")
        audio_controller.stop_playback()
        gesture_tracker.release()
        cap.release()
        cv2.destroyAllWindows()
        print("Done!")

if __name__ == "__main__":
    main()
