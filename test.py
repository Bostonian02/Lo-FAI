import httpx
import asyncio
import json
import base64
from playsound import playsound
import tempfile
import os

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

async def play_audio_and_request(url, alpha, seed, prompt):
    alpha_rollover = False
    alpha_velocity = 0.25
    while True:
        payload = make_payload(alpha, prompt, seed)

        response = await run_inference(url, data=payload)

        if response is not None:
            response_data = json.loads(response)
            if 'audio' in response_data:
                base64_encoded_audio = response_data['audio']
                binary_audio_data = base64.b64decode(base64_encoded_audio)
            else:
                print("No audio data in the response")
        else:
            print("POST request failed")
        
        # Play audio concurrently
        play_audio_task = asyncio.to_thread(playsound, binary_audio_data)

        # Wait for both tasks to complete
        await play_audio_task

        new_alpha = alpha + alpha_velocity
        if (new_alpha > 1 + 1e-3):
            new_alpha = new_alpha - 1
            alpha_rollover = True
        alpha = new_alpha

        if (alpha_rollover):
            seed = seed + 1
            alpha_rollover = False

        


async def main():
    url = 'http://192.168.1.1:3013/run_inference/'
    alpha = 0.25
    seed = 808
    prompt = "funky jazz solo"

    # while True:
    #     payload = make_payload(alpha, prompt, seed)

    #     if (preloaded_audio_data is None):
    #         response = await run_inference(url, data=payload)

    #         if response is not None:
    #             response_data = json.loads(response)
    #             new_alpha = alpha + alpha_velocity
    #             if (new_alpha > 1 + 1e-3):
    #                 new_alpha = new_alpha - 1
    #                 alpha_rollover = True
    #             alpha = new_alpha
    #             if 'audio' in response_data:
    #                 base64_encoded_audio = response_data['audio']
    #                 print(base64_encoded_audio)
    #                 binary_audio_data = base64.b64decode(base64_encoded_audio)
    #                 play_audio(binary_audio_data)
    #         else:
    #             print("POST request failed.")
    #     else:
    #         play_audio(preloaded_audio_data)
        
    #     if (alpha_rollover):
    #         seed = seed + 1
    #         alpha_rollever = False
        
    #     await preload_audio(url, make_payload(alpha, prompt, seed))
    asyncio.run(play_audio_and_request(url, alpha, seed, prompt))

def play_audio(binary_audio_data):
    temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    temp_audio_file.write(binary_audio_data)
    temp_audio_file.close()
    playsound(temp_audio_file.name)
    os.remove(temp_audio_file.name)

def make_payload(alpha, prompt, seed):
    payload = {
        "alpha": alpha,
        "seed_image_id": "vibes",
        "num_inference_steps": 50,
        "start": {
            "denoising": 0.75,
            "guidance": 7,
            "prompt": prompt,
            "seed": seed
        },
        "end": {
            "denoising": 0.75,
            "guidance": 7,
            "prompt": prompt,
            "seed": seed + 1
        }
    }
    return payload

if __name__ == '__main__':
    asyncio.run(main())