import discord
from discord import app_commands
from discord.ext import tasks
import json
import os
import psutil
import datetime
import time
from flask import Flask
from threading import Thread
from dotenv import load_dotenv # โหลดโมดูลอ่านไฟล์ .env

# --- โหลดตัวแปรจากไฟล์ .env ---
load_dotenv()

# --- Web Server สำหรับ Uptimerobot ---
app = Flask('')

@app.route('/')
def home():
    return "I'm alive! PDR Community Bot is running."

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- การตั้งค่าไฟล์ ---
CONFIG_FILE = 'welcome_config.json'
BANNED_WORDS_FILE = 'banned_words.json'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def load_banned_words():
    if not os.path.exists(BANNED_WORDS_FILE):
        default_words = ["ควย", "เย็ด", "มึง", "กู", "สัส", "เหี้ย"]
        save_banned_words(default_words)
        return default_words
    with open(BANNED_WORDS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_banned_words(words):
    with open(BANNED_WORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(words, f, indent=4, ensure_ascii=False)

# --- ตั้งค่าบอท ---
intents = discord.Intents.default()
intents.members = True 
intents.message_content = True 

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.start_time = time.time()
        self.banned_words = load_banned_words()

    async def on_ready(self):
        await self.tree.sync()
        self.update_status.start()
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print(f'System Ready! Loaded {len(self.banned_words)} banned words.')

    async def on_message(self, message):
        if message.author.bot: return
        if message.author.guild_permissions.administrator: return

        content = message.content.lower()
        if "discord.gg/" in content or "discord.com/invite/" in content:
            await message.delete()
            warning = await message.channel.send(f"🚫 {message.author.mention} **ห้ามส่งลิงก์เชิญเซิร์ฟเวอร์อื่นนะคะ!**")
            await warning.delete(delay=5)
            return

        for word in self.banned_words:
            if word in content:
                await message.delete()
                warning = await message.channel.send(f"⚠️ {message.author.mention} **โปรดใช้คำสุภาพด้วยค่ะ!**")
                await warning.delete(delay=5)
                return

    # --- แก้ไข Loop: ปรับเป็น 30 วินาที เพื่อแก้ Error 429 ---
    @tasks.loop(seconds=30) 
    async def update_status(self):
        try:
            ping = round(self.latency * 1000)
            
            # --- แก้ Error Termux: ใส่ Try/Except ดักจับ CPU ---
            try:
                process = psutil.Process(os.getpid())
                ram_usage = process.memory_info().rss / 1024 / 1024 
                cpu_usage = process.cpu_percent() / psutil.cpu_count()
            except Exception:
                ram_usage = 0
                cpu_usage = 0

            total_members = sum(guild.member_count for guild in self.guilds)
            
            current_time = time.time()
            uptime_seconds = int(current_time - self.start_time)
            uptime_string = str(datetime.timedelta(seconds=uptime_seconds))

            statuses = [
                f"🛡️ Security Active | Banned: {len(self.banned_words)} words",
                f"RAM: {ram_usage:.1f}MB | Ping: {ping}ms",
                f"Serving {total_members} Users",
                "Welcome to PDR Community!"
            ]

            current_status = statuses[int(time.time() / 30) % len(statuses)] # หาร 30 ตามเวลา Loop
            await self.change_presence(activity=discord.Game(name=current_status))
            
        except Exception as e:
            print(f"Status Error: {e}")

    async def on_member_join(self, member):
        config = load_config()
        guild_id = str(member.guild.id)
        if guild_id in config:
            channel_id = config[guild_id]
            channel = self.get_channel(channel_id)
            if channel:
                message = (
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎉 **ยินดีต้อนรับเข้าสู่ PDR Community** 🎉\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"👋 สวัสดีค่ะ คุณ {member.mention}\n"
                    f"> ยินดีต้อนรับเข้าสู่ครอบครัวของเราอย่างเป็นทางการค่ะ!\n\n"
                    f"💡 **สิ่งที่คุณทำได้ที่นี่:**\n"
                    f"• พูดคุยกับเพื่อนสมาชิกและแลกเปลี่ยนความคิดเห็น\n"
                    f"• ติดต่อทีมงานได้ทันทีหากต้องการความช่วยเหลือ\n\n"
                    f"ขอให้มีความสุขกับการใช้งานนะคะ 💖\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                )
                await channel.send(message)

client = MyClient()

# --- Slash Commands ---
@client.tree.command(name="ping", description="เช็คสถานะระบบและความปลอดภัย")
async def ping(interaction: discord.Interaction):
    ping = round(client.latency * 1000)
    try:
        process = psutil.Process(os.getpid())
        ram = process.memory_info().rss / 1024 / 1024
        cpu = process.cpu_percent() / psutil.cpu_count()
    except:
        ram = 0
        cpu = 0
    
    current_time = time.time()
    uptime_seconds = int(current_time - client.start_time)
    uptime = str(datetime.timedelta(seconds=uptime_seconds))
    
    embed = discord.Embed(title="🛡️ PDR Security System Status", color=0xf1c40f)
    embed.add_field(name="📡 Ping", value=f"`{ping}ms`", inline=True)
    embed.add_field(name="💾 RAM", value=f"`{ram:.2f} MB`", inline=True)
    embed.add_field(name="💻 CPU", value=f"`{cpu:.1f}%`", inline=True)
    embed.add_field(name="⏱️ Uptime", value=f"`{uptime}`", inline=False)
    embed.add_field(name="🔒 Protection", value=f"`Active`", inline=False)
    embed.set_footer(text="PDR Community System")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ... (คำสั่งอื่นๆ add_word, remove_word, list_words, set_welcome, test_welcome ใช้ของเดิมได้เลยค่ะ) ...
# เพื่อไม่ให้โค้ดยาวเกินไป ผมละไว้ แต่ถ้าจะก๊อปให้ครบ ย้อนไปดูอันเก่านิดนึงแล้วเปลี่ยนแค่ส่วนบนตามนี้นะคะ

@client.tree.command(name="help", description="ดูรายการคำสั่งทั้งหมด")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="📚 คำสั่งของ PDR Community Bot", description="รายชื่อคำสั่งทั้งหมด", color=0xf1c40f)
    embed.add_field(name="🛠️ `/set_welcome`", value="ตั้งค่าห้องต้อนรับ", inline=False)
    embed.add_field(name="🛡️ `/ping`", value="ดูสถานะระบบ", inline=False)
    embed.set_footer(text="PDR Community System")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@client.tree.command(name="set_welcome", description="ตั้งค่าห้องต้อนรับ")
async def set_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ ต้องเป็น Admin ค่ะ", ephemeral=True)
        return
    config = load_config()
    config[str(interaction.guild_id)] = channel.id
    save_config(config)
    await interaction.response.send_message(f"✅ ตั้งค่าห้องต้อนรับเป็น {channel.mention} แล้วค่ะ", ephemeral=True)

@client.tree.command(name="test_welcome", description="ทดสอบต้อนรับ")
async def test_welcome(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ ต้องเป็น Admin ค่ะ", ephemeral=True)
        return
    await client.on_member_join(interaction.user)
    await interaction.response.send_message("✅ ทดสอบแล้วค่ะ", ephemeral=True)

# เริ่ม Web Server
keep_alive()

# --- ดึง Token จาก .env ---
token = os.getenv('TOKEN')

if token:
    client.run(token)
else:
    print("❌ ไม่พบ Token! กรุณาตรวจสอบไฟล์ .env หรือ Environment Variable บน Render ค่ะ")
        
