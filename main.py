import discord
from discord import app_commands
import json
import os
import datetime
import time
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

# โหลด .env
load_dotenv()

# --- Web Server (Keep Alive) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Config ---
CONFIG_FILE = 'welcome_config.json'

def load_config():
    if not os.path.exists(CONFIG_FILE): return {}
    with open(CONFIG_FILE, 'r') as f: return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f: json.dump(config, f, indent=4)

# --- Bot Setup ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.start_time = time.time()

    async def on_ready(self):
        await self.tree.sync()
        await self.change_presence(activity=discord.Game(name="Welcome to PDR Community"))
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('>>> Bot is Ready <<<')

    async def on_member_join(self, member):
        config = load_config()
        guild_id = str(member.guild.id)
        if guild_id in config:
            channel_id = config[guild_id]
            channel = self.get_channel(channel_id)
            if channel:
                # ข้อความต้อนรับ
                msg = (
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
                await channel.send(msg)

client = MyClient()

# --- Slash Commands ---

@client.tree.command(name="ping", description="เช็คสถานะ")
async def ping(interaction: discord.Interaction):
    latency = round(client.latency * 1000)
    current_time = time.time()
    seconds = int(current_time - client.start_time)
    uptime = str(datetime.timedelta(seconds=seconds))
    
    embed = discord.Embed(title="🤖 Bot Status", color=0xf1c40f)
    embed.add_field(name="Ping", value=f"{latency}ms", inline=True)
    embed.add_field(name="Uptime", value=f"{uptime}", inline=True)
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
    await interaction.response.send_message("✅ ทดสอบเรียบร้อยค่ะ", ephemeral=True)

@client.tree.command(name="help", description="ดูคำสั่งทั้งหมด")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="📚 คำสั่งของ PDR Community Bot", color=0xf1c40f)
    embed.add_field(name="⚙️ จัดการ", value="`/set_welcome`, `/test_welcome`", inline=False)
    embed.add_field(name="ℹ️ ข้อมูล", value="`/ping`", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# เริ่มระบบ
keep_alive()

token = os.getenv('TOKEN')
if token:
    client.run(token)
else:
    print("❌ ไม่พบ Token")
    
