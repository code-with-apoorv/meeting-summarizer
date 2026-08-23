"""
Generates sample meeting audio files for testing the Meeting Summarizer.
Creates a valid WAV audio file using standard library modules (wave, struct, math).
"""

import os
import wave
import struct
import math
from pathlib import Path

def create_synthetic_wav(filename: str, duration_sec: int = 5, sample_rate: int = 16000):
    output_path = Path(__file__).parent / filename
    num_samples = duration_sec * sample_rate
    
    with wave.open(str(output_path), 'w') as wav_file:
        # Mono, 16-bit, sample_rate
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        # Generate simulated audio wave pattern
        for i in range(num_samples):
            t = i / sample_rate
            # Mix a few speech-frequency harmonic frequencies (300Hz, 800Hz, 1500Hz) with gentle modulation
            freq = 440 + 50 * math.sin(2 * math.pi * 2 * t)
            envelope = math.sin(math.pi * (t % 0.8) / 0.8) if (t % 1.0) < 0.8 else 0.05
            value = int(16000 * envelope * math.sin(2 * math.pi * freq * t))
            # Clamp value
            value = max(-32767, min(32767, value))
            data = struct.pack('<h', value)
            wav_file.writeframes(data)
            
    print(f"Generated sample audio: {output_path} ({duration_sec}s, {sample_rate}Hz)")
    return output_path

if __name__ == "__main__":
    create_synthetic_wav("sample_meeting_demo.wav", duration_sec=6)
    create_synthetic_wav("sample_sprint_planning.wav", duration_sec=4)
