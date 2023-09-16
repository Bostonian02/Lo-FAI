import json
import requests
import io
import base64
from PIL import Image, PngImagePlugin

url = "http://127.0.0.1:7860"

#PROMPT FROM RIFFUSION OR TWITCH CHAT
prompt = "soft jazz" 

payload = {
    "prompt": "visual representation of "+ prompt +" music",
    "steps": 20
}

response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)

r = response.json()

print(r) #just testing

#taking base64 string and converting it to a useable image
image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))

png_payload = {
    "image": "data:image/png;base64," + i
}
response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)

pnginfo = PngImagePlugin.PngInfo()
pnginfo.add_text("parameters", response2.json().get("info"))

#saving image to local for now. have to get this into OBS automatically somehow
image.save('output.png', pnginfo=pnginfo)