# 4K Stable fiffusion telegram bot
Create a Stable Diffusion Telegram Bot which allows you to generate images in the bot via the API of the stable diffusion interface 
the resulution can be changed in HD or in 4K which uses the upscaler.

## Setup
- You need to install this repro: 
https://github.com/AUTOMATIC1111/stable-diffusion-webui 

- Enable the API by adding this line to your webui.bat file: 
<code>set COMMANDLINE_ARGS=--api --xformers --listen --enable-insecure-extension-access</code> 

- Get a key from the @botfather and put this in the key.txt file
run the script by <code>python3 run_main.py</code> 

## commands
- /get  and then put your search promt here 
- /cfg [number] the cfg you would set in the Gui standard its set to 14 
- /sr [number 1 or 2] change the resolution to 1920 x 1080 or to 4K 

## Video is coming soon
