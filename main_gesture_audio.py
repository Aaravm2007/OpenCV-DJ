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
            
            # Display status on frame with percentages
            status = audio_controller.get_status()
            
            # Convert values to percentages (based on -2.0 to +2.0 range for EQ, 0-2 for volume)
            bass_pct = int((status['bass'] + 2.0) / 4.0 * 100)
            treble_pct = int((status['treble'] + 2.0) / 4.0 * 100)
            speech_pct = int((status['speech'] + 2.0) / 4.0 * 100)
            volume_pct = int(status['volume'] / 2.0 * 100)
            
            # Create semi-transparent overlay for better readability
            overlay = processed_frame.copy()
            cv2.rectangle(overlay, (5, 5), (320, 240), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, processed_frame, 0.4, 0, processed_frame)
            
            # Display parameters with percentages and progress bars
            y_offset = 35
            
            # Bass
            cv2.putText(processed_frame, f"BASS: {bass_pct}%", (15, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.rectangle(processed_frame, (140, y_offset-18), (300, y_offset-5), (50, 50, 50), -1)
            cv2.rectangle(processed_frame, (140, y_offset-18), (140 + int(bass_pct * 1.6), y_offset-5), (0, 255, 0), -1)
            y_offset += 35
            
            # Treble
            cv2.putText(processed_frame, f"TREBLE: {treble_pct}%", (15, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.rectangle(processed_frame, (140, y_offset-18), (300, y_offset-5), (50, 50, 50), -1)
            cv2.rectangle(processed_frame, (140, y_offset-18), (140 + int(treble_pct * 1.6), y_offset-5), (0, 255, 0), -1)
            y_offset += 35
            
            # Speech Clarity
            cv2.putText(processed_frame, f"SPEECH: {speech_pct}%", (15, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.rectangle(processed_frame, (140, y_offset-18), (300, y_offset-5), (50, 50, 50), -1)
            cv2.rectangle(processed_frame, (140, y_offset-18), (140 + int(speech_pct * 1.6), y_offset-5), (0, 255, 0), -1)
            y_offset += 35
            
            # Volume
            cv2.putText(processed_frame, f"VOLUME: {volume_pct}%", (15, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.rectangle(processed_frame, (140, y_offset-18), (300, y_offset-5), (50, 50, 50), -1)
            cv2.rectangle(processed_frame, (140, y_offset-18), (140 + int(volume_pct * 1.6), y_offset-5), (255, 255, 0), -1)
            y_offset += 35
            
            # Effects
            echo_color = (0, 255, 255) if status['echo'] == "ON" else (100, 100, 100)
            reverb_color = (0, 255, 255) if status['reverb'] == "ON" else (100, 100, 100)
            
            cv2.putText(processed_frame, f"ECHO: {status['echo']}", (15, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, echo_color, 2)
            y_offset += 35
            cv2.putText(processed_frame, f"REVERB: {status['reverb']}", (15, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, reverb_color, 2)
            
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
