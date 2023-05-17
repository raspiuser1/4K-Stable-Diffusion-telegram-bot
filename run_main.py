import asyncio
import os
import time
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import json
import requests
import io
import base64
from PIL import Image, PngImagePlugin
import sys
from io import BytesIO
import time



res = 2
cfg = 8
ff = open("key.txt").readline().rstrip()
# Set up Telegram bot
bot = Bot(token=ff)
#put this in your webui.bat
#set COMMANDLINE_ARGS=--api
#set COMMANDLINE_ARGS=--listen

url = "http://192.168.1.90:7860"

def refresh_checkpoints(update, context):
    endpoint = f'{url}/sdapi/v1/refresh-checkpoints'
    headers = {'accept': 'application/json'}
    response = requests.post(endpoint, headers=headers)
    if response.status_code == 200:
        #msg = "Checkpoints Stable diffusion refreshed successfully."
        msg = get_ram_usage()
        print(msg)
        update.message.reply_text(msg)
        return True
    else:
        msg = f"Failed to refresh Stable diffusion checkpoints. Status code: {response.status_code}"
        print(msg)
        update.message.reply_text(msg)
        return False    


def get_ram_usage():
    # Define the URL and headers for the request
    url2 =  f'{url}/sdapi/v1/memory'
    headers = {'accept': 'application/json'}
    # Send the GET request and retrieve the response
    response = requests.get(url2, headers=headers)
    # Extract the RAM usage information from the response JSON
    ram_info = response.json()['ram']

    free_ram = round(ram_info['free'] / (1024 ** 3),1)
    used_ram = round(ram_info['used'] / (1024 ** 3),1)
    total_ram = round(ram_info['total'] / (1024 ** 3),1)
    # Return the RAM usage information
    ram_msg = '========RAM USAGE(GB)========\nfree: ' + str(free_ram) + '\nused: ' + str(used_ram) + '\ntotal: ' + str(total_ram)
    return ram_msg

def print_model_names(api_url):
    response = requests.get(api_url)
    response_json = response.json()

    for model in response_json:
        print(model["model_name"])

def get_options():
    url1 = f'{url}/sdapi/v1/options'
    headers = {'accept': 'application/json'}
    response = requests.get(url1, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print('Error fetching options:', response.status_code)
        return None


def stablediff(prompt2,update, context):
    if res == 1:
        w = 768
        h = 512
        update.message.reply_text("Scaling to 3072x2048")
        #scaled: 3072x2048
    if res == 2:
        w = 480
        h = 270
        update.message.reply_text("Scaling to 1920x1080")
        #scaled: 1920x1080
    data ={}
    try:
        with open('stabledif_setting.json', 'r') as f:
            data = json.load(f)
    except :
        pass

    payload = {
        "prompt": f"{prompt2}, " + data.get("prompt", "high resolution, good quality, sharp, very detailed, colour"),
        "steps": data.get("steps", 60),
        #"sampler_name": "DPM++ 2M Karras",
        "cfg_scale": cfg,
        "restore_faces" : data.get("restore_faces", True),
        "negative_prompt": data.get("negative_prompt", "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"),
        "width" : w,
        "height" : h
    }

    #save the json, it will be loaded everytime on start of this function
    if not os.path.isfile('stabledif_setting.json'):
        with open('stabledif_setting.json', 'w') as f:
            json.dump(payload, f)

    start_time = time.time()
    print("starting stable diffusion")
    response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
    r = response.json()

    end_time = time.time()

    duration = round(end_time - start_time,1)

    print(r.get("parameters"))
    #print(json.dumps( , indent=4))
    print(f"Duration get image: {duration} seconds")
    try:
        if r.get("detail") == "Not Found":
            # do something
            print("Variable not found!")
        else:
            try:
                for i in r['images']:
                    image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))

                    png_payload = {
                        "image": "data:image/png;base64," + i
                    }
                    response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)

                    pnginfo = PngImagePlugin.PngInfo()
                    pnginfo.add_text("parameters", response2.json().get("info"))
                    imgname = "image_out" + get_unix_time() + ".png"
  
                    image.save(imgname)
                    start_time = time.time()
                    img7 = scale(imgname,update, context)                
                    end_time = time.time()
                    #os.remove(imgname) 
                    duration2 = round(end_time - start_time,1)
                    dur3 = round(duration + duration2,1)
                    msg1 = (f"Duration scaling image: {duration2} seconds")
                    msg2 = (f"Total duration {dur3}")
                    update.message.reply_text(msg1 + "\n" + msg2)
                    return(img7)
            except:
                print("Error getting image")        
    except:
        print("Cannot connect to: " + url)            


def get_unix_time():
    return str(int(time.time()))



def pil_to_base64(pil_image):
    """Encode PIL Image to base64 string."""
    with BytesIO() as stream:
        meta = PngImagePlugin.PngInfo()
        for k, v in pil_image.info.items():
            if isinstance(k, str) and isinstance(v, str):
                meta.add_text(k, v)
        pil_image.save(stream, "PNG", pnginfo=meta)
        base64_str = str(base64.b64encode(stream.getvalue()), "utf-8")
        return "data:image/png;base64," + base64_str


def scale(imgname,update, context):
    API_URL = url + "/sdapi/v1/extra-batch-images"

    # Get files without directories or subdirectories
    # image_names = [f for f in os.listdir(DIR_IN) if os.path.isfile(os.path.join(DIR_IN, f))]
    print("Upscaling images...")
    update.message.reply_text("Upscaling images...") 
    image_list = []
    # for i in image_names:
    #     image_list.append({"data": pil_to_base64(Image.open(DIR_IN + i)), "name": i})
    #     print(i)
    image_list.append({"data": pil_to_base64(Image.open(imgname)), "name": imgname})
    payload = {
        "resize_mode": 0,
        "gfpgan_visibility": 0,
        "codeformer_visibility": 0,
        "codeformer_weight": 0,
        "upscaling_resize": 4,
        "upscaler_1": "R-ESRGAN 4x+",
        "upscaler_2": "None",
        "extras_upscaler_2_visibility": 0,
        "imageList": image_list,
        "upscale_first": False  # upscale before restoring faces (not
        # applied if visibility = 0?)
    }

    payloadJson = json.dumps(payload)
    resp = requests.post(url=API_URL, data=payloadJson).json()

    if resp.get("images") is None:
        print("extras.py: Error, Post response:")
        print(resp)
        sys.exit(1)

    else:
        index = 0
        for i in resp["images"]:
            index = index + 1
            metadata = PngImagePlugin.PngInfo()
            img = Image.open(io.BytesIO(base64.b64decode(i)))
            for key, value in img.info.items():
                if isinstance(key, str) and isinstance(value, str):
                    metadata.add_text(key, value)
            img6 = "scaled_" + imgname      
            img.save(
                img6,
                "PNG",
                pnginfo=metadata,
            )
        print("Done scaling")
        print(img6)
        return(img6)

def get_image(update, context):
    message = update.message
    text = message.text
    # Check if the message starts with a '/'
    if text.startswith('/'):
        # Split the command and arguments
        args = text[5:]
        # get stable dif image
        if refresh_checkpoints(update, context):
                #here we can continue as we have a connection
                scaledimage = stablediff(args,update, context)
                #send the file through telegram
                with open(scaledimage, "rb") as file2:
                    context.bot.send_document(chat_id=update.message.chat_id, document=file2)


def cfg_set(update, context):
    global cfg
    message = update.message
    text = message.text
    # Check if the message starts with a '/'
    if text.startswith('/'):
        # Split the command and arguments
        parts = text.split(' ')
        try:
            args = int(parts[1])
            cfg = args
        except:
            update.message.reply_text("Wrong Argument, a number is required") 


def set_resolution(update, context):
    global res
    message = update.message
    text = message.text
    # Check if the message starts with a '/'
    if text.startswith('/'):
        # Split the command and arguments
        parts = text.split(' ')
        try:
            args = int(parts[1].strip())
            if args == 1:
                res = args
                update.message.reply_text("Scaled resolution changed to 3072x2048")
            elif args == 2:
                res = args
                update.message.reply_text("Scaled resolution changed to 1920x1080")
            else:
                update.message.reply_text("Resolution Argument missing:\n1 for: 3072x2048 \n2 for 1920x1080")    
        except:
            update.message.reply_text("Wrong Argument:\n1 for: 3072x2048 \n2 for 1920x1080") 

def main():
    # Start the updater and get the dispatcher
    updater = Updater(token=ff, use_context=True)
    dispatcher = updater.dispatcher
    # Add command handlers
    dispatcher.add_handler(CommandHandler("get", get_image))
    dispatcher.add_handler(CommandHandler("cfg", cfg_set))
    dispatcher.add_handler(CommandHandler("sr", set_resolution))
    # Start the updater
    updater.start_polling()
    # Keep the program running
    updater.idle()


if __name__ == "__main__":
    main()