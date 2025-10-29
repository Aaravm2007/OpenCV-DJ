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
import numpy as np
from gesture_tracker import GestureTracker
from audio_controller import AudioController

AUDIO_FILE = "song.mp3"  # Change this to your audio file path


def print_status(status):
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

    try:
        audio_controller = AudioController(AUDIO_FILE)
        gesture_tracker = GestureTracker()
    except Exception as e:
        print(f"Error initializing components: {e}")
        sys.exit(1)

    # Start audio playback
    audio_controller.start_playback()
    print("Audio playback started!")

    # Try opening webcam
    cap = cv2.VideoCapture(0)
    camera_available = cap.isOpened()

    if camera_available:
        print("✅ Camera detected! Starting gesture control.")
    else:
        print("⚠️ Warning: Camera not detected. Running in No-Input Mode.")

    # Always create the display window
    cv2.namedWindow('Gesture-Controlled Audio Mixer', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Gesture-Controlled Audio Mixer', 900, 600)
    cv2.moveWindow('Gesture-Controlled Audio Mixer', 100, 100)

    print("\nGesture Control Active!")
    print("=" * 80)
    print("LEFT HAND:  ↑=Bass+  ↓=Bass-  →=Treble+  ←=Treble-  Rotate=Echo Toggle")
    print("RIGHT HAND: ↑=Vol+   ↓=Vol-   →=Speech+  ←=Speech-  Rotate=Reverb Toggle")
    print("=" * 80)
    print("\nPress 'q' to quit\n")

    try:
        while True:
            if camera_available:
                ret, frame = cap.read()
                if not ret:
                    print("⚠️ No frame read from camera.")
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(frame, "Camera Error - No Input",
                                (120, 250), cv2.FONT_HERSHEY_SIMPLEX,
                                1.0, (0, 0, 255), 2)
                else:
                    frame = cv2.flip(frame, 1)
                    processed_frame, actions = gesture_tracker.process_frame(frame)

                    if actions:
                        for action in actions:
                            audio_controller.handle_action(action)

                    status = audio_controller.get_status()
                    display_status(processed_frame, status)
                    print_status(status)
                    cv2.imshow('Gesture-Controlled Audio Mixer', processed_frame)
            else:
                # Show static no-input frame
                no_input_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(no_input_frame, "No Camera Input Detected",
                            (100, 250), cv2.FONT_HERSHEY_SIMPLEX,
                            1.0, (0, 0, 255), 2)
                cv2.imshow('Gesture-Controlled Audio Mixer', no_input_frame)

            # Refresh display
            key = cv2.waitKey(10) & 0xFF
            if key == ord('q'):
                break

    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    finally:
        print("\nCleaning up...")
        audio_controller.stop_playback()
        if camera_available:
            gesture_tracker.release()
            cap.release()
        cv2.destroyAllWindows()
        print("✅ Done!")


def display_status(frame, status):
    bass_pct = int((status['bass'] + 2.0) / 4.0 * 100)
    treble_pct = int((status['treble'] + 2.0) / 4.0 * 100)
    speech_pct = int((status['speech'] + 2.0) / 4.0 * 100)
    volume_pct = int(status['volume'] / 2.0 * 100)

    overlay = frame.copy()
    cv2.rectangle(overlay, (5, 5), (320, 240), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    y_offset = 35
    draw_bar(frame, "BASS", bass_pct, y_offset, (0, 255, 0)); y_offset += 35
    draw_bar(frame, "TREBLE", treble_pct, y_offset, (0, 255, 0)); y_offset += 35
    draw_bar(frame, "SPEECH", speech_pct, y_offset, (0, 255, 0)); y_offset += 35
    draw_bar(frame, "VOLUME", volume_pct, y_offset, (255, 255, 0)); y_offset += 35

    echo_color = (0, 255, 255) if status['echo'] == "ON" else (100, 100, 100)
    reverb_color = (0, 255, 255) if status['reverb'] == "ON" else (100, 100, 100)
    cv2.putText(frame, f"ECHO: {status['echo']}", (15, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, echo_color, 2)
    y_offset += 35
    cv2.putText(frame, f"REVERB: {status['reverb']}", (15, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, reverb_color, 2)


def draw_bar(frame, label, percent, y, color):
    cv2.putText(frame, f"{label}: {percent}%", (15, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.rectangle(frame, (140, y - 18), (300, y - 5), (50, 50, 50), -1)
    cv2.rectangle(frame, (140, y - 18), (140 + int(percent * 1.6), y - 5), color, -1)


if __name__ == "__main__":
    main()
