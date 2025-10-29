import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy import signal
import threading
import time

class AudioController:
    def __init__(self, audio_file):
        # Load audio file
        self.audio_data, self.sample_rate = sf.read(audio_file)
        
        # Convert stereo to mono if needed
        if len(self.audio_data.shape) > 1:
            self.audio_data = np.mean(self.audio_data, axis=1)
        
        # Audio parameters
        self.bass_gain = 0.0
        self.treble_gain = 0.0
        self.speech_gain = 0.0
        self.volume = 1.0
        
        # Filter states
        self.echo_enabled = False
        self.reverb_enabled = False
        
        # Adjustment step size
        self.step_size = 0.1
        self.volume_step = 0.05
        
        # Playback control
        self.is_playing = False
        self.current_position = 0
        self.playback_thread = None
        self.lock = threading.Lock()
        
    def apply_eq(self, audio_chunk):
        """Apply EQ adjustments (bass, treble, speech clarity)"""
        # Design filters
        nyquist = self.sample_rate / 2
        
        # Bass boost/cut (20-250 Hz)
        if abs(self.bass_gain) > 0.01:
            low_freq = 250 / nyquist
            b_bass, a_bass = signal.butter(2, low_freq, btype='low')
            bass = signal.filtfilt(b_bass, a_bass, audio_chunk)
            audio_chunk = audio_chunk + bass * self.bass_gain
        
        # Treble boost/cut (4000+ Hz)
        if abs(self.treble_gain) > 0.01:
            high_freq = 4000 / nyquist
            b_treble, a_treble = signal.butter(2, high_freq, btype='high')
            treble = signal.filtfilt(b_treble, a_treble, audio_chunk)
            audio_chunk = audio_chunk + treble * self.treble_gain
        
        # Speech clarity (1000-3000 Hz)
        if abs(self.speech_gain) > 0.01:
            low_speech = 1000 / nyquist
            high_speech = 3000 / nyquist
            b_speech, a_speech = signal.butter(2, [low_speech, high_speech], btype='band')
            speech = signal.filtfilt(b_speech, a_speech, audio_chunk)
            audio_chunk = audio_chunk + speech * self.speech_gain
        
        return audio_chunk
    
    def apply_echo(self, audio_chunk, delay=0.3, decay=0.5):
        """Apply echo effect"""
        delay_samples = int(delay * self.sample_rate)
        output = np.copy(audio_chunk)
        
        if len(audio_chunk) > delay_samples:
            output[delay_samples:] += audio_chunk[:-delay_samples] * decay
        
        return output
    
    def apply_reverb(self, audio_chunk, decay=0.3):
        """Apply simple reverb effect"""
        delays = [0.029, 0.037, 0.041, 0.043]
        output = np.copy(audio_chunk)
        
        for i, delay in enumerate(delays):
            delay_samples = int(delay * self.sample_rate)
            if len(audio_chunk) > delay_samples:
                output[delay_samples:] += audio_chunk[:-delay_samples] * decay * (0.8 ** i)
        
        return output
    
    def process_audio(self, audio_chunk):
        """Apply all active effects to audio chunk"""
        with self.lock:
            # Apply EQ
            processed = self.apply_eq(audio_chunk)
            
            # Apply echo
            if self.echo_enabled:
                processed = self.apply_echo(processed)
            
            # Apply reverb
            if self.reverb_enabled:
                processed = self.apply_reverb(processed)
            
            # Apply volume
            processed = processed * self.volume
            
            # Normalize to prevent clipping
            max_val = np.max(np.abs(processed))
            if max_val > 1.0:
                processed = processed / max_val
            
            return processed
    
    def audio_callback(self, outdata, frames, time_info, status):
        """Callback for audio stream"""
        with self.lock:
            start = self.current_position
            end = start + frames
            
            if end > len(self.audio_data):
                # Loop audio
                chunk = np.concatenate([
                    self.audio_data[start:],
                    self.audio_data[:end - len(self.audio_data)]
                ])
                self.current_position = end - len(self.audio_data)
            else:
                chunk = self.audio_data[start:end]
                self.current_position = end
            
            # Process audio
            processed = self.process_audio(chunk)
            
            # Output
            outdata[:] = processed.reshape(-1, 1)
    
    def start_playback(self):
        """Start audio playback"""
        if not self.is_playing:
            self.is_playing = True
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=1,
                callback=self.audio_callback
            )
            self.stream.start()
    
    def stop_playback(self):
        """Stop audio playback"""
        if self.is_playing:
            self.is_playing = False
            self.stream.stop()
            self.stream.close()
    
    def handle_action(self, action):
        """Handle gesture action"""
        with self.lock:
            if action == "increase_bass":
                self.bass_gain = min(2.0, self.bass_gain + self.step_size)
            elif action == "decrease_bass":
                self.bass_gain = max(-2.0, self.bass_gain - self.step_size)
            
            elif action == "increase_treble":
                self.treble_gain = min(2.0, self.treble_gain + self.step_size)
            elif action == "decrease_treble":
                self.treble_gain = max(-2.0, self.treble_gain - self.step_size)
            
            elif action == "increase_volume":
                self.volume = min(2.0, self.volume + self.volume_step)
            elif action == "decrease_volume":
                self.volume = max(0.0, self.volume - self.volume_step)
            
            elif action == "increase_speech":
                self.speech_gain = min(2.0, self.speech_gain + self.step_size)
            elif action == "decrease_speech":
                self.speech_gain = max(-2.0, self.speech_gain - self.step_size)
            
            elif action == "toggle_echo":
                self.echo_enabled = not self.echo_enabled
            
            elif action == "toggle_reverb":
                self.reverb_enabled = not self.reverb_enabled
    
    def get_status(self):
        """Get current audio parameters"""
        with self.lock:
            return {
                "bass": round(self.bass_gain, 2),
                "treble": round(self.treble_gain, 2),
                "speech": round(self.speech_gain, 2),
                "volume": round(self.volume, 2),
                "echo": "ON" if self.echo_enabled else "OFF",
                "reverb": "ON" if self.reverb_enabled else "OFF"
            }
