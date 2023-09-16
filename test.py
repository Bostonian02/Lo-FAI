import httpx
import asyncio
import json
import base64
from playsound import playsound
import tempfile
import os
import random
import math
from pydub import AudioSegment
from io import BytesIO
import pygame
import math
import numpy as np

class RealTimeUpsampler:
    def __init__(self, input_rate, output_rate):
        self.input_rate = input_rate
        self.output_rate = output_rate
        self.ratio = output_rate / input_rate

    def linear_interpolate(self, data):
        indices = np.arange(0, len(data) - 1, 1 / self.ratio)
        indices_floor = np.floor(indices).astype(int)
        alpha = indices - indices_floor
        upsampled = (1 - alpha) * data[indices_floor] + alpha * data[indices_floor + 1]
        return upsampled.astype(data.dtype)

# Initial starting seeds depending on seed map
initialSeedImageMap = {
    "og_beat": [3, 738973, 674, 745234, 808, 231, 3324, 323984, 123, 51209, 123, 51209, 6754, 8730],
    "agile": [808, 231, 3324, 323984],
    "marim": [123, 51209, 6754, 8730],
    "motorway": [8730, 323984, 745234],
    "vibes": [4205, 94, 78530]
}

# Initial seed maps
initialSeeds = [
    "og_beat",
    "agile",
    "marim",
    "motorway",
    "vibes"
]

# Audio clip length
AUDIO_LENGTH = 5.11

# Initialize pygame mixer outside of play_audio
pygame.mixer.init(frequency=88200)

# Global variable to store binary audio data
binary_audio_data = None

async def get_binary_audio_data(url, data):
    global binary_audio_data
    response = await run_inference(url, data=data)

    if response is not None:
        response_data = json.loads(response)
        if 'audio' in response_data:
            base64_encoded_audio = response_data['audio']
            binary_audio_data = base64.b64decode(base64_encoded_audio)
        else:
            print("No audio data in the response")
    else:
        print("POST request failed")

async def run_inference(url, data):
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            json_data = json.dumps(data)
            headers={"Content-Type": "application/json"}
            response = await client.post(url, data=json_data, headers=headers)
            response.raise_for_status() #Raise an exception for non-2xx codes
            return response.text
        except httpx.HTTPError as e:
            print(f"HTTP Error occurred: {e}")
            return None

async def play_audio_and_request(url, alpha, seed, seed_image_id, prompt_a, prompt_b):
    global binary_audio_data
    
    alpha_rollover = False
    alpha_velocity = 0.25

    # Initially load the first audio data
    await get_binary_audio_data(url, make_payload(alpha, prompt_a, prompt_b, seed_image_id, seed))

    while True:
        # Convert the current audio to WAV
        upsampler = RealTimeUpsampler(44100, 88200)
        wav_data = convert_to_wav(binary_audio_data, upsampler)
        song = pygame.mixer.Sound(BytesIO(wav_data))

        # Update alpha for the next payload
        new_alpha = alpha + alpha_velocity
        if new_alpha > 1 + 1e-3:
            new_alpha = new_alpha - 1
            alpha_rollover = True
        alpha = new_alpha

        # Check if alpha has rolled over
        if alpha_rollover:
            seed += 1
            alpha_rollover = False
            if prompt_a != prompt_b:
                prompt_a = prompt_b

        # Start playing the current audio
        play_audio_task = asyncio.to_thread(song.play)

        # While the current audio is playing, preload and convert the next one
        preload_audio_task = await asyncio.to_thread(get_binary_audio_data, url, make_payload(alpha, prompt_a, prompt_b, seed_image_id, seed))

        # Wait a constant amount of time so that there is good spacing between audio segments
        wait_audio_task = await asyncio.to_thread(asyncio.sleep, 5.05)

        # Run the tasks concurrently
        await asyncio.gather(play_audio_task, preload_audio_task, wait_audio_task)

        # Wait until the current audio finishes playing before proceeding to the next iteration
        # while pygame.mixer.get_busy():
        #     pygame.time.Clock().tick()

# Convert mp3 data to wav since that's what PyGame supports
# def convert_to_wav(mp3_audio):
#     mp3 = AudioSegment.from_mp3(BytesIO(mp3_audio))
#     buffer = BytesIO()
#     mp3.export(buffer, format="wav")
#     return buffer.getvalue()

# Convert mp3 data to wav (and upscale it) since that's what PyGame supports
def convert_to_wav(mp3_audio, upsampler):
    mp3 = AudioSegment.from_mp3(BytesIO(mp3_audio))
    samples = np.array(mp3.get_array_of_samples())
    upsampled_samples = upsampler.linear_interpolate(samples)
    upsampled_audio = AudioSegment(upsampled_samples.tobytes(), frame_rate=88200, sample_width=mp3.sample_width, channels=mp3.channels)
    buffer = BytesIO()
    upsampled_audio.export(buffer, format="wav")
    return buffer.getvalue()

def make_payload(alpha, prompt_a, prompt_b, seed_image_id, seed):
    payload = {
        "alpha": alpha,
        "seed_image_id": seed_image_id,
        "num_inference_steps": 50,
        "start": {
            "denoising": 0.75,
            "guidance": 7,
            "prompt": prompt_a,
            "seed": seed
        },
        "end": {
            "denoising": 0.75,
            "guidance": 7,
            "prompt": prompt_b,
            "seed": seed + 1
        }
    }
    return payload

if __name__ == '__main__':
    url = 'http://192.168.1.1:3013/run_inference/'
    alpha = 0.25
    seed_image_id = initialSeeds[math.floor(random.random() * len(initialSeeds))]
    seed = initialSeedImageMap[seed_image_id][math.floor(random.random() * len(initialSeedImageMap[seed_image_id]))]
    prompt = "calm lo-fi music"
    asyncio.run(play_audio_and_request(url, alpha, seed, seed_image_id, prompt, prompt))
