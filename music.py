import asyncio
from collections import deque
import math
import numpy as np
import pyaudio
from pywizlight import wizlight, PilotBuilder
import time

# --- Configuration ---
# Light IP
LIGHT_IP = "192.168.1.6"

# Gain / Sensitivity
# Increase this if your piano is quiet, decrease if it's too loud.
SENSITIVITY = 1.0

# Audio parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
MIN_DB_THRESHOLD = -50  # Ignore sound below this dB (noise floor)

# Setup PyAudio
p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

# Shared state between audio task and light task
shared_state = {
    "brightness": 0,
    "rgb": (0, 0, 0),
    "updated": False
}


def pitch_to_color(frequency):
    """
    Maps a frequency (pitch) to an RGB color with abrupt changes.
    """
    if frequency < 250:
        return (255, 0, 0)  # Red (Low bass)
    elif frequency < 400:
        return (255, 165, 0)  # Orange
    elif frequency < 600:
        return (255, 255, 0)  # Yellow
    elif frequency < 1000:
        return (0, 255, 0)  # Green (Mid range)
    elif frequency < 2000:
        return (0, 128, 255)  # Sky Blue
    elif frequency < 4000:
        return (0, 0, 255)  # Blue
    else:
        return (128, 0, 128)  # Purple (High notes)


def volume_to_brightness(volume_db):
    """
    Maps volume (dB) to brightness [10, 255].
    volume_db usually ranges from roughly -60 (quiet) to 0 (clipping).
    """
    # Assuming -50 is quiet and -5 is very loud
    raw_brightness = np.interp(volume_db, [-50, -5], [10, 255])

    if raw_brightness >= 255:
        return 255
    elif raw_brightness <= 10:
        return 0  # Off or minimum
    else:
        # Snap to multiples of 25 for slightly stepped brightness
        brightness = int(round((raw_brightness - 10) / 25) * 25)
        return min(brightness, 255)


async def audio_task():
    """
    Reads audio in a non-blocking thread, analyzes pitch and volume,
    and updates the shared state.
    """
    print("🎙️ Audio listener started...")

    # Pre-calculate frequency bins for FFT
    fft_freqs = np.fft.rfftfreq(CHUNK, 1.0 / RATE)

    try:
        while True:
            # Read audio data in a separate thread so we don't block asyncio
            data = await asyncio.to_thread(stream.read, CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)

            # --- Volume (dB) Calculation ---
            # Apply SENSITIVITY gain
            audio_data_float = audio_data.astype(np.float32) * SENSITIVITY

            rms = np.sqrt(np.mean(audio_data_float ** 2))
            volume_db = 20 * np.log10(rms / 32768.0 + 1e-6) + 10
            volume_db = max(volume_db, -100)

            # --- Pitch (FFT) Calculation ---
            if volume_db > MIN_DB_THRESHOLD:
                # Only calculate FFT if it's loud enough (not just background noise)
                # Apply Hanning window to reduce spectral leakage
                windowed = audio_data_float * np.hanning(len(audio_data_float))
                fft_result = np.fft.rfft(windowed)
                magnitudes = np.abs(fft_result)

                # Find the index of the maximum magnitude
                peak_idx = np.argmax(magnitudes)
                dominant_freq = fft_freqs[peak_idx]

                new_rgb = pitch_to_color(dominant_freq)
                new_brightness = volume_to_brightness(volume_db)
            else:
                new_rgb = (0, 0, 0)
                new_brightness = 0

            # Update shared state if something changed
            if new_brightness != shared_state["brightness"] or new_rgb != shared_state["rgb"]:
                shared_state["brightness"] = new_brightness
                shared_state["rgb"] = new_rgb
                shared_state["updated"] = True

                print(f"Freq: {dominant_freq:.1f}Hz | dB: {volume_db:.1f} | RGB: {new_rgb} | Bri: {new_brightness}")

    except asyncio.CancelledError:
        print("Audio task stopped.")


async def light_task():
    """
    Reads from the shared state at a fixed rate and updates the WiZ bulb.
    This prevents spamming the bulb with too many requests.
    """
    print("💡 Light controller started...")
    bulb = wizlight(LIGHT_IP)
    last_sent_brightness = None
    last_sent_rgb = None

    try:
        while True:
            if shared_state["updated"]:
                b = shared_state["brightness"]
                c = shared_state["rgb"]

                # Turn off if brightness is 0
                if b == 0:
                    if last_sent_brightness != 0:
                        await bulb.turn_off()
                        last_sent_brightness = 0
                else:
                    if b != last_sent_brightness or c != last_sent_rgb:
                        await bulb.turn_on(PilotBuilder(brightness=b, rgb=c))
                        last_sent_brightness = b
                        last_sent_rgb = c

                shared_state["updated"] = False

            # Rate Limit: max ~20 updates per second
            await asyncio.sleep(0.05)

    except asyncio.CancelledError:
        print("Light task stopped.")
        await bulb.turn_off()


async def main():
    print("🚀 Starting Piano-to-Light Engine (Press Ctrl+C to stop)...")

    # Run both tasks concurrently
    task1 = asyncio.create_task(audio_task())
    task2 = asyncio.create_task(light_task())

    try:
        await asyncio.gather(task1, task2)
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
    finally:
        task1.cancel()
        task2.cancel()
        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    # Use try-except here to catch KeyboardInterrupt gracefully on Windows/Mac
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
