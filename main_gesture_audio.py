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
            
            # Handle detected actions
            if actions and audio_controller:
                for action in actions:
                    audio_controller.handle_action(action)
            
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
            
            # Display status on frame
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
