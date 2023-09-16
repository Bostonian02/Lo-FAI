import json
import requests
import io
import base64
import sys
from PIL import Image, PngImagePlugin

url = "http://127.0.0.1:7860"

#PROMPT WILL COME FROM TWITCH CHAT EVENTUALLY
cleaned_args = [arg.strip('\'"') for arg in sys.argv[1:]]
prompt = ' '.join(cleaned_args)

with open('prompt.txt', 'w') as file:
    file.write(prompt)


#adding the keyword "dreamscape" to the prompt SIGNIFICANTLY decreases odds of getting people
#it does result in oversaturated colorful psychedelic images
#they look dope but idk if that's the vibe. i like results more when dreamscape not in the prompt
payload = {
    "prompt": "(representation of "+ prompt +" music:1.5), beautiful artwork, 8k, highest resolution",
    "negative_prompt": "(human:1.5), (person:1.5), (grainy:1.3), grid, people, man, woman, nude, naked, nsfw, porn, text, portrait, watermark, signature, (words:1.5), (letters:1.5)",
    "steps": 20,
    "cfg_scale": 7,
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
    #saving PNG. pygame takes it and puts it in the stream window hopefully lmao
    image.save('output.png', pnginfo=pnginfo)