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
import json
import requests
import io
import base64
from PIL import Image, PngImagePlugin

# Global queue for next prompt
next_prompt_queue = queue.Queue()

# ... [Twitch bot related imports and code] ...

def twitch_connect(bot_nick, channel, oauth_token):
    server = 'irc.chat.twitch.tv'
    port = 6697  # Updated to Twitch's SSL port

    # Create a socket
    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Create an SSL context
    context = ssl.create_default_context()

    # Wrap the socket with SSL
    irc = context.wrap_socket(irc, server_hostname=server)

    # Connect to the server
    irc.connect((server, port))

    # Send authentication and join messages
    irc.send(f"PASS {oauth_token}\r\n".encode('utf-8'))
    irc.send(f"NICK {bot_nick}\r\n".encode('utf-8'))
    irc.send(f"JOIN #{channel}\r\n".encode('utf-8'))

    # Receive and print the server's response
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
    oauth_token = "oauth:bzjdpmnvjlff2l6pgj80hdfr4yq6d8"

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
            set_next_prompt(next_prompt)

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

# Next prompt queue
next_prompt_queue = queue.Queue()

# Global variable for current prompt
current_prompt = "calming lofi"

# Global current prompt queue
current_prompt_queue = queue.Queue()

# Get current prompt
def get_current_prompt():
    return peek_current_prompt()

# Transitioning variable
transitioning = False

# Initialize pygame mixer outside of play_audio
pygame.mixer.init(frequency=88200)

# Global variable to store binary audio data
binary_audio_data = None

# Setter method for the next prompt
def set_next_prompt(prompt):
    next_prompt_queue.put(prompt)

# Setter method for current prompt
def set_current_prompt(prompt):
    while not current_prompt_queue.empty():
        current_prompt_queue.get_nowait()
    current_prompt_queue.put(prompt)

# Getter method for the next prompt
def get_next_prompt():
    try:
        return next_prompt_queue.get_nowait()
    except queue.Empty:
        return get_current_prompt()

# Peek at the next prompt without removing it from the queue.  
def peek_next_prompt():
    try:
        # Temporarily get the next prompt
        prompt = next_prompt_queue.get_nowait()
        # Immediately put it back to ensure it's not removed
        next_prompt_queue.put(prompt)
        return prompt
    except queue.Empty:
        return None

# Peek at the current prompt without removing it from the queue
def peek_current_prompt():
    try:
        prompt = current_prompt_queue.get_nowait()
        current_prompt_queue.put(prompt)
        return prompt
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
    global transitioning
    global current_prompt
    
    alpha_rollover = False
    alpha_velocity = 0.25

    # Initially load the first audio data
    await get_binary_audio_data(url, make_payload(alpha, prompt_a, prompt_b, seed_image_id, seed))

    while True:
        # Check if there's a new prompt and we're not already transitioning
        if not next_prompt_queue.empty() and not transitioning:
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

        # Set prompt_a and prompt_b based on transitioning state and next_prompt_queue
        next_in_queue = peek_next_prompt()
        if transitioning and next_in_queue:
            # prompt_a = current_prompt
            prompt_a = get_current_prompt()
            prompt_b = next_in_queue
        else:
            curr_prompt = get_current_prompt()
            prompt_a = curr_prompt
            prompt_b = curr_prompt

        # Check if alpha has rolled over
        if alpha_rollover:
            seed += 1
            alpha_rollover = False
            if transitioning:
                # current_prompt = get_next_prompt()
                set_current_prompt(get_next_prompt())
                transitioning = False
        
        # Make next payload
        next_payload = make_payload(alpha, prompt_a, prompt_b, seed_image_id, seed)

        # Start playing the current audio
        play_audio_task = asyncio.to_thread(song.play)

        # While the current audio is playing, preload and convert the next one
        preload_audio_task = await asyncio.to_thread(get_binary_audio_data, url, next_payload)

        # Wait a constant amount of time so that there is good spacing between audio segments
        wait_audio_task = await asyncio.to_thread(asyncio.sleep, 5.05)

        # Run the tasks concurrently
        await asyncio.gather(play_audio_task, preload_audio_task, wait_audio_task)

async def update_SD_art():
    url = "http://127.0.0.1:7860/"

    user_input = get_current_prompt()
    while True:
        await asyncio.sleep(5)  # Add a delay to prevent high CPU usage

        prev_input = user_input
        user_input = get_current_prompt()
        print(f"Previous Prompt: {prev_input}, Current Prompt: {user_input}")  # Print prompts for debugging
        if user_input == prev_input:
            continue
        prompt = user_input

        with open('prompt.txt', 'w') as file:
            file.write(prompt)

        payload = {
            "prompt": "(representation of "+ prompt +" music:1.5), beautiful artwork, 8k, highest resolution",
            "negative_prompt": "(human:1.5), (person:1.5), (grainy:1.3), grid, people, man, woman, nude, naked, nsfw, porn, text, portrait, watermark, signature, (words:1.5), (letters:1.5)",
            "steps": 20,
            "cfg_scale": 7,
         }

        async with httpx.AsyncClient() as client:
            response = await client.post(f'{url}/sdapi/v1/txt2img', json=payload)
            r = response.json()

            # Assuming you only want the first image
            if r['images']:
                i = r['images'][0]
                image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))

                png_payload = {
                    "image": "data:image/png;base64," + i
                }
                response2 = await client.post(f'{url}/sdapi/v1/png-info', json=png_payload)

                pnginfo = PngImagePlugin.PngInfo()
                pnginfo.add_text("parameters", response2.json().get("info"))
                image.save('output.png', pnginfo=pnginfo)

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
    image_generator_thread = threading.Thread(target=asyncio.run, args=(update_SD_art()))

    twitch_bot_thread.start()
    audio_generator_thread.start()
    image_generator_thread.start()

    twitch_bot_thread.join()
    audio_generator_thread.join()
    image_generator_thread.join()

if __name__ == '__main__':
    url = 'http://192.168.1.1:3013/run_inference/'
    alpha = 0.25
    seed_image_id = initialSeeds[math.floor(random.random() * len(initialSeeds))]
    seed = initialSeedImageMap[seed_image_id][math.floor(random.random() * len(initialSeedImageMap[seed_image_id]))]
    try:
        run_bot_and_audio()
    except KeyboardInterrupt:
        threading.Event().set()
