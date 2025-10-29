🎧 Gesture-Controlled DJ Mixer
Control music using just your hands — no touch, no mouse, just motion.

This project lets you mix and modify a local song in real-time using hand gestures tracked through your webcam.
Built with OpenCV, MediaPipe, and Python, it uses your left and right hands to adjust bass, treble, volume, and speech clarity — and even apply live filters like echo or reverb based on hand rotation.

🌀 Demo

🎥 Coming soon!
Once the project is running, your webcam feed will appear with live gesture overlays while the song’s sound dynamically changes in response.

🚀 Features
Feature	Description
🖐️ Dual-hand tracking	Detects and distinguishes left vs right hands in real time using MediaPipe
🎚️ Live audio control	Adjust bass, treble, volume, and speech clarity via hand movement
🔄 Rotation filters	Rotate left or right hand to toggle echo or reverb effects
🧠 Intelligent smoothing	Gesture data is averaged over frames for stable control
🎵 Local file playback	Works with .mp3 or .wav songs stored on your computer
💻 Modular code	Clean separation between gesture detection, audio control, and main loop
🧠 Gesture Mappings
Hand	Motion	Effect
✋ Left hand ↑	Increase Bass	
✋ Left hand ↓	Decrease Bass	
✋ Left hand →	Increase Treble	
✋ Left hand ←	Decrease Treble	
🤚 Right hand ↑	Increase Volume	
🤚 Right hand ↓	Decrease Volume	
🤚 Right hand →	Increase Speech Clarity (boost 1–3 kHz)	
🤚 Right hand ←	Decrease Speech Clarity	
↻ Left hand rotation	Toggle Echo filter	
↻ Right hand rotation	Toggle Reverb filter	
🏗️ Project Structure
gesture-dj-mixer/
│
├── main.py                # Main loop connecting camera and audio engine
├── gesture_tracker.py     # Handles MediaPipe hand tracking and gesture recognition
├── audio_controller.py    # Applies EQ, volume, and filters to the song
├── requirements.txt       # All Python dependencies
└── README.md              # Project documentation

⚙️ Installation

Clone the repository

git clone https://github.com/yourusername/gesture-dj-mixer.git
cd gesture-dj-mixer


Install dependencies

pip install -r requirements.txt


or manually:

pip install opencv-python mediapipe numpy pydub scipy sounddevice


Add your song

Place a .mp3 or .wav file in the project directory.

Rename it to song.mp3 or update the filename in audio_controller.py.

Run the program

python main.py

🧩 How It Works

Hand Tracking – MediaPipe detects 21 landmarks per hand and distinguishes left vs right.

Gesture Recognition – Movement and rotation deltas (Δx, Δy, angle) are analyzed each frame.

Action Mapping – Each motion direction is mapped to a specific audio control (e.g., bass↑).

Audio Processing – The local song is continuously filtered using pydub and scipy.signal.

Feedback – The camera window overlays the detected gestures and active filters live.

🎚️ Audio Controls

Bass & Treble: Adjusted by low-pass and high-pass filters.

Speech Clarity: Boosts mid frequencies around 1–3 kHz.

Volume: Overall gain control in decibels.

Echo / Reverb: Simple convolution filters triggered by hand rotation.

🧠 Technical Notes

Movement smoothing via a moving average to reduce jitter.

Rotation thresholds (~15°) used to prevent false filter toggles.

Modular threading ensures continuous playback while processing video.

Can be extended to use sounddevice streaming for near-zero latency DSP.

🧩 Example Console Output
Detected: Left hand ↑ → Bass +2
Detected: Right hand ↓ → Volume -3
Active Filters: Echo [ON], Reverb [OFF]
Bass: +6 | Treble: +2 | Volume: -1 | Speech: +3

🛠️ Future Enhancements

 Real-time FFT visualization overlay

 Gesture calibration for individual users

 Multi-song playlist control

 Integration with Spotify for visual controls (no audio processing)

 Lighting / LED sync with music intensity

🧑‍💻 Tech Stack
Layer	Tools
Hand Tracking	MediaPipe + OpenCV
Audio DSP	Pydub, Scipy
Playback	SoundDevice
Language	Python 3.10+
Platform	Cross-platform (Windows / macOS / Linux)
💡 Inspiration

Inspired by touchless interfaces and virtual DJ systems — built to reimagine how we interact with music using pure motion and creativity.

📜 License

MIT License © 2025 [Your Name]
