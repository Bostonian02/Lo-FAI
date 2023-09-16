import json
import requests
import io
import base64
from PIL import Image, PngImagePlugin

url = "http://127.0.0.1:7860"

#PROMPT WILL COME TWITCH CHAT EVENTUALLY
prompt = "soft jazz"

payload = {
    "prompt": "visual representation of "+ prompt +" music",
    "negative_prompt": "human, text, words, letters",
    "steps": 20
}

response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)

r = response.json()

#breaks when i try to take it out of the for loop and i can't be fucked to fix it
#loop will only run once
#taking the base64 image data and converting it to a PNG
for i in r['images']:
    image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))

    png_payload = {
        "image": "data:image/png;base64," + i
    }
    response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)

    pnginfo = PngImagePlugin.PngInfo()
    pnginfo.add_text("parameters", response2.json().get("info"))
    #saving PNG. not sure where this should go. so here it goes.
    image.save('output.png', pnginfo=pnginfo)