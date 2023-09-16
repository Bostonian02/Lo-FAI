import httpx
import asyncio
import json

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

async def main():
    url = 'http://192.168.1.1:3013/run_inference/'

    payload = {
        "alpha": 0.25,
        "seed_image_id": "vibes",
        "num_inference_steps": 50,
        "start": {
            "denoising": 0.75,
            "guidance": 7,
            "prompt": "funky synth solo",
            "seed": 808
        },
        "end": {
            "denoising": 0.75,
            "guidance": 7,
            "prompt": "funky synth solo",
            "seed": 809
        }
    }

    print(payload)

    response = await run_inference(url, data=payload)

    if response is not None:
        print(f"POST Response:\n{response}")
    else:
        print("POST request failed.")


if __name__ == '__main__':
    asyncio.run(main())