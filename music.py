import asyncio
from collections import deque
from time import sleep
import math
import numpy as np
import pyaudio
from pywizlight import wizlight, PilotBuilder

# Audio parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# Light IP
LIGHT_IP = "192.168.1.4"

# Setup PyAudio
p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)


def volume_to_brightness(volume, max_volume=500):
    """
    Maps volume to brightness in intervals of 50, starting at 10, capped at 255.
    """
    volume = min(volume, max_volume)
    raw_brightness = np.interp(volume, [0, max_volume], [10, 255])

    if raw_brightness >= 255:
        return 255
    else:
        # Round to nearest multiple of 50 starting from 0
        brightness = int(round((raw_brightness - 10) / 50) * 50)
        return min(brightness, 250)


async def main():
    bulb = wizlight(LIGHT_IP)
    last_brightness = None
    volume_history = deque(maxlen=5)  # For smoothing

    print("🎙️ Listening... Press Ctrl+C to stop")
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            volume = int(np.linalg.norm(audio_data) / CHUNK)

            volume_history.append(volume)
            smooth_volume = int(np.mean(volume_history))

            brightness = volume_to_brightness(smooth_volume)

            if brightness != last_brightness:
                await bulb.turn_on(PilotBuilder(brightness=brightness))
                last_brightness = brightness

            #print(f"Volume: {smooth_volume} → Brightness: {brightness}")

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        await bulb.turn_off()  # Optional: turn off the bulb on exit


async def main2():
    bulb = wizlight(LIGHT_IP)
    last_brightness = None
    last_rgb = None
    volume_history = deque(maxlen=5)

    print("🎙️ Listening... Press Ctrl+C to stop")
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            volume = int(np.linalg.norm(audio_data) / CHUNK)

            volume_history.append(volume)
            smooth_volume = int(np.mean(volume_history))
            brightness = volume_to_brightness(smooth_volume)

            # Determine RGB color based on volume level
            if smooth_volume < 20:
                rgb = (0, 0, 255)  # Blue
            elif smooth_volume < 40:
                rgb = (0, 128, 255)  # Sky Blue
            elif smooth_volume < 60:
                rgb = (0, 255, 0)  # Green
            elif smooth_volume < 80:
                rgb = (255, 255, 0)  # Yellow
            elif smooth_volume < 100:
                rgb = (255, 165, 0)  # Orange
            else:
                rgb = (255, 0, 0)  # Red

            if brightness != last_brightness or rgb != last_rgb:
                await bulb.turn_on(PilotBuilder(brightness=10, rgb=rgb))
                last_brightness = brightness
                last_rgb = rgb

                print(f"Volume: {smooth_volume} → Brightness: {brightness}, Color: {rgb}, smooth: {smooth_volume}, volume history: {volume_history}")
            # sleep(0.05)

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        await bulb.turn_off()

async def db_vol():
    bulb = wizlight(LIGHT_IP)
    last_brightness = None
    last_rgb = None
    volume_history = deque(maxlen=5)

    print("🎙️ Listening... Press Ctrl+C to stop")
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)

            # Calculate RMS (Root Mean Square)
            rms = np.sqrt(np.mean(audio_data.astype(np.float32)**2))
            volume_db = 20 * np.log10(rms / 32768.0 + 1e-6) +10 # Add small value to avoid log(0)
            volume_db = max(volume_db, -100)  # Clamp minimum for stability

            volume_history.append(volume_db)
            smooth_volume_db = np.mean(volume_history)
            brightness = volume_to_brightness(smooth_volume_db)

            # Map dB to RGB (example thresholds, you can tune)
            if smooth_volume_db < -50:
                rgb = (0, 0, 255)  # Blue
            elif smooth_volume_db < -20:
                rgb = (0, 128, 255)  # Sky Blue
            elif smooth_volume_db < -15:
                rgb = (0, 255, 0)  # Green
            elif smooth_volume_db < -10:
                rgb = (255, 255, 0)  # Yellow
            elif smooth_volume_db < -5:
                rgb = (255, 165, 0)  # Orange
            else:
                rgb = (255, 0, 0)  # Red

            if brightness != last_brightness or rgb != last_rgb:
                await bulb.turn_on(PilotBuilder(brightness=150, rgb=rgb))
                last_brightness = brightness
                last_rgb = rgb

                # print(f"dB: {volume_db:.2f} → Brightness: {brightness}, Color: {rgb}, smooth dB: {smooth_volume_db:.2f}, history: {list(volume_history)}")
            print(f"dB: {volume_db:.2f}")
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        await bulb.turn_off()

if __name__ == "__main__":
    asyncio.run(db_vol())
