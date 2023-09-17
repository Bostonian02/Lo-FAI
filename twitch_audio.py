import socket
import asyncio
import random
import ssl
import httpx
import json
import base64
import math
from pydub import AudioSegment
from io import BytesIO
import pygame
import numpy as np
import threading
import queue

# Global queue for next prompt
next_prompt_queue = queue.Queue()

# ... [Twitch bot related imports and code] ...

def twitch_connect(bot_nick, channel, oauth_token):
    server = 'irc.chat.twitch.tv'
    port = 6697

    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    irc = ssl.wrap_socket(irc)  # Wrap the socket for SSL
    irc.connect((server, port))

    irc.send(f"PASS {oauth_token}\r\n".encode('utf-8'))
    irc.send(f"NICK {bot_nick}\r\n".encode('utf-8'))
    irc.send(f"JOIN #{channel}\r\n".encode('utf-8'))
    response = irc.recv(2048).decode('utf-8')
    print(response)

    return irc

suggestions = []  # List to store the suggestions

async def send_message(irc, channel, message):
    """Send a message to the Twitch channel."""
    irc.send(f"PRIVMSG #{channel} :{message}\r\n".encode('utf-8'))

async def main():
    bot_nick = "lo_fai"
    channel = "lo_fai"
    oauth_token = "oauth:iu06wjmcdcb7b8x9u18logfgdjfmh2"

    irc = twitch_connect(bot_nick, channel, oauth_token)
    
    while True:
        try:
            response = await asyncio.to_thread(irc.recv, 2048)
            response = response.decode('utf-8')

            if response.startswith('PING'):
                irc.send("PONG :tmi.twitch.tv\r\n".encode('utf-8'))
                continue
            else:
                print(response)

            await asyncio.gather(
                asyncio.sleep(30),
                look_for_suggestions(response, irc, channel)
            )

            next_prompt = await return_popular_response()
            print("The next prompt is: " + next_prompt)
            await set_next_prompt(next_prompt)

        except ConnectionResetError:
            print("Connection was reset. Trying to reconnect...")
            irc = twitch_connect(bot_nick, channel, oauth_token)


async def look_for_suggestions(response, irc, channel):
    global suggestions

    if ("PRIVMSG" not in response):
        return
    user = response.split('!', 1)[0][1:]
    message = response.split('PRIVMSG', 1)[1].split(':', 1)[1].strip()

    # If message starts with !suggest
    if message.startswith('!suggest'):
        # Split the message by spaces
        parts = message.split()
        # If there are more parts after !suggest, we consider them the suggestion
        if len(parts) > 1:
            suggestion = ' '.join(parts[1:])
            print(suggestion + " has been added to suggestions")
            suggestions.append(suggestion)
            await send_message(irc, channel, f"Your suggestion {suggestion} has been added.")

# Finish this
async def return_popular_response():
    global suggestions

    if not suggestions:
        return "calming lo-fi"
    chosen_suggestion = random.choice(suggestions)
    suggestions.clear()
    return chosen_suggestion

# ... [Audio generator related imports and code] ...

# Upsampler for the model's audio
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

# Global variable for next prompt
next_prompt = None

# Global flag
next_prompt_changed = False

next_prompt_lock = threading.Lock()

# Global variable for current prompt
current_prompt = "calming lofi"

# Get current prompt
def get_current_prompt():
    global current_prompt
    return current_prompt

# Transitioning variable
transitioning = False

# Audio clip length
AUDIO_LENGTH = 5.11

# Initialize pygame mixer outside of play_audio
pygame.mixer.init(frequency=88200)

# Global variable to store binary audio data
binary_audio_data = None

# Setter method for the next prompt
async def set_next_prompt(prompt):
    global next_prompt
    with next_prompt_lock:
        if not next_prompt:
            next_prompt = prompt

# Getter method for the next prompt
def get_next_prompt():
    try:
        return next_prompt_queue.get_nowait()
    except queue.Empty:
        return None

# Get binary audio data from the inference model response
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

# Make a request to the inference model
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
    global next_prompt
    global next_prompt_changed
    global transitioning
    global current_prompt
    
    alpha_rollover = False
    alpha_velocity = 0.25

    # Initially load the first audio data
    await get_binary_audio_data(url, make_payload(alpha, prompt_a, prompt_b, seed_image_id, seed))

    while True:
        if get_next_prompt() and not transitioning:
            print("we are transitioning")
            transitioning = True
            alpha = 0.25
        
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

        if transitioning:
            if (alpha_rollover):
                current_prompt = get_next_prompt()
                set_next_prompt(None)
                transitioning = False

        # Check if alpha has rolled over
        if alpha_rollover:
            seed += 1
            alpha_rollover = False
        
        # Make next payload
        next_payload = make_payload(alpha, current_prompt, current_prompt if not get_next_prompt() else get_next_prompt(), seed_image_id, seed)

        # Start playing the current audio
        play_audio_task = asyncio.to_thread(song.play)

        # While the current audio is playing, preload and convert the next one
        preload_audio_task = await asyncio.to_thread(get_binary_audio_data, url, next_payload)

        # Wait a constant amount of time so that there is good spacing between audio segments
        wait_audio_task = await asyncio.to_thread(asyncio.sleep, 5.05)

        # Run the tasks concurrently
        await asyncio.gather(play_audio_task, preload_audio_task, wait_audio_task)

# Convert mp3 data to wav (and upscale it) since that's what PyGame supports
def convert_to_wav(mp3_audio, upsampler):
    mp3 = AudioSegment.from_mp3(BytesIO(mp3_audio))
    samples = np.array(mp3.get_array_of_samples())
    upsampled_samples = upsampler.linear_interpolate(samples)
    upsampled_audio = AudioSegment(upsampled_samples.tobytes(), frame_rate=88200, sample_width=mp3.sample_width, channels=mp3.channels)
    buffer = BytesIO()
    upsampled_audio.export(buffer, format="wav")
    return buffer.getvalue()

# Generate JSON payload for inference model
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


# Create separate threads for the Twitch bot and audio generator
def run_bot_and_audio():
    twitch_bot_thread = threading.Thread(target=asyncio.run, args=(main(),))
    audio_generator_thread = threading.Thread(target=asyncio.run, args=(play_audio_and_request(url, alpha, seed, seed_image_id, current_prompt, current_prompt),))

    twitch_bot_thread.start()
    audio_generator_thread.start()

    twitch_bot_thread.join()
    audio_generator_thread.join()

if __name__ == '__main__':
    url = 'http://192.168.1.1:3013/run_inference/'
    alpha = 0.25
    seed_image_id = initialSeeds[math.floor(random.random() * len(initialSeeds))]
    seed = initialSeedImageMap[seed_image_id][math.floor(random.random() * len(initialSeedImageMap[seed_image_id]))]
    run_bot_and_audio()
