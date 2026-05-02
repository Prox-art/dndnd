import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import json
import os
import random
import dotenv

# تحميل متغيرات البيئة من ملف .env
dotenv.load_dotenv()

# إعدادات البوت - استخدام التوكن من ملف .env
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    raise ValueError("❌ لم يتم العثور على DISCORD_TOKEN في ملف .env")

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        super().__init__(command_prefix="!", intents=intents)
        self.tokens_data = self.load_data()
        self.active_tasks = {}
        self.auto_react_channels = []

    def load_data(self):
        if os.path.exists('data_v2.json'):
            with open('data_v2.json', 'r') as f:
                return json.load(f)
        return {
            "tokens": [], 
            "clans": {}, 
            "clan_messages": {},
            "settings": {"auto_status": True}
        }

    def save_data(self):
        with open('data_v2.json', 'w') as f:
            json.dump(self.tokens_data, f, indent=4)

    async def setup_hook(self):
        await self.tree.sync()
        self.status_rotator.start()
        print(f"Synced slash commands for {self.user}")

    @tasks.loop(minutes=5)
    async def status_rotator(self):
        if self.tokens_data["settings"].get("auto_status"):
            statuses = [discord.Status.online, discord.Status.idle, discord.Status.dnd]
            await self.change_presence(status=random.choice(statuses))

bot = MyBot()

# --- أوامر الإدارة الأساسية ---

@bot.tree.command(name="add", description="إضافة توكنات حسابات (بحد أقصى 20)")
async def add_tokens(interaction: discord.Interaction, tokens_list: str):
    new_tokens = tokens_list.replace(',', ' ').split()
    added = 0
    for t in new_tokens:
        if len(bot.tokens_data["tokens"]) < 20 and t not in bot.tokens_data["tokens"]:
            bot.tokens_data["tokens"].append(t)
            added += 1
    bot.save_data()
    await interaction.response.send_message(f"✅ تم إضافة {added} توكن. الإجمالي: {len(bot.tokens_data['tokens'])}/20")

@bot.tree.command(name="add_clan", description="إضافة توكنات إلى فريق معين")
async def add_clan(interaction: discord.Interaction, clan_name: str, tokens: str):
    target_tokens = tokens.replace(',', ' ').split()
    if clan_name not in bot.tokens_data["clans"]:
        bot.tokens_data["clans"][clan_name] = []
    added = 0
    for t in target_tokens:
        if t in bot.tokens_data["tokens"] and t not in bot.tokens_data["clans"][clan_name]:
            bot.tokens_data["clans"][clan_name].append(t)
            added += 1
    bot.save_data()
    await interaction.response.send_message(f"✅ تم إضافة {added} توكن إلى الفريق '{clan_name}'.")

# --- ميزات التمويه والرسائل ---

@bot.tree.command(name="set_clan_msg", description="تحديد رسالة عشوائية يرسلها الكلان للتمويه")
async def set_clan_msg(interaction: discord.Interaction, clan_name: str, message: str):
    if clan_name not in bot.tokens_data["clans"]:
        await interaction.response.send_message("❌ الكلان غير موجود.")
        return
    bot.tokens_data["clan_messages"][clan_name] = message
    bot.save_data()
    await interaction.response.send_message(f"✅ تم تحديد رسالة التمويه لكلان {clan_name}: {message}")

@bot.tree.command(name="join_voice", description="توجيه فريق للفويس مع تأخير عشوائي للتمويه")
async def join_voice(interaction: discord.Interaction, clan_name: str, channel_id: str):
    if clan_name not in bot.tokens_data["clans"]:
        await interaction.response.send_message("❌ الكلان غير موجود.")
        return
    
    tokens = bot.tokens_data["clans"][clan_name]
    await interaction.response.send_message(f"🚀 جاري إدخال {len(tokens)} توكن بتأخير عشوائي للتمويه...")
    
    for token in tokens:
        delay = random.uniform(2.0, 8.0)
        await asyncio.sleep(delay)
        print(f"Token {token[:5]} joined {channel_id} after {delay:.2f}s")

# --- ميزات الفزعة والتفاعل ---

@bot.tree.command(name="fazaa", description="أمر الفزعة: توجيه كل التوكنات لروم واحد فوراً")
async def fazaa(interaction: discord.Interaction, channel_id: str):
    all_tokens = bot.tokens_data["tokens"]
    await interaction.response.send_message(f"🚨 فززززعة! جاري توجيه {len(all_tokens)} توكن إلى الروم {channel_id}...")
    for token in all_tokens:
        await asyncio.sleep(0.5)
        print(f"Token {token[:5]} rushing to {channel_id}")

@bot.tree.command(name="auto_react_setup", description="تفعيل مراقبة قناة للرياكشن التلقائي")
async def auto_react_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    if channel.id not in bot.auto_react_channels:
        bot.auto_react_channels.append(channel.id)
        await interaction.response.send_message(f"👀 البوت الآن يراقب {channel.mention}. أي رياكشن تضعه سيقوم التوكنات بتقليده.")
    else:
        bot.auto_react_channels.remove(channel.id)
        await interaction.response.send_message(f"🛑 تم إيقاف مراقبة {channel.mention}.")

@bot.event
async def on_raw_reaction_add(payload):
    if payload.channel_id in bot.auto_react_channels:
        print(f"New reaction detected: {payload.emoji}. Tokens will mimic...")

@bot.tree.command(name="mass_react", description="جعل التوكنات تتفاعل مع رسالة معينة بايموجي محدد")
async def mass_react(interaction: discord.Interaction, message_id: str, emoji: str):
    await interaction.response.send_message(f"✅ جاري وضع رياكشن {emoji} على الرسالة {message_id} بواسطة جميع التوكنات.")

# --- الإحصائيات ---

@bot.tree.command(name="stats", description="عرض إحصائيات البوت والتوكنات")
async def stats(interaction: discord.Interaction):
    total_tokens = len(bot.tokens_data["tokens"])
    total_clans = len(bot.tokens_data["clans"])
    
    embed = discord.Embed(title="📊 إحصائيات البوت المتقدمة", color=discord.Color.blue())
    embed.add_field(name="إجمالي التوكنات", value=f"`{total_tokens}/20`", inline=True)
    embed.add_field(name="عدد الكلانات", value=f"`{total_clans}`", inline=True)
    
    clans_info = ""
    for name, tks in bot.tokens_data["clans"].items():
        msg_status = "✅" if name in bot.tokens_data["clan_messages"] else "❌"
        clans_info += f"• **{name}**: {len(tks)} توكن (رسالة: {msg_status})\n"
    
    if clans_info:
        embed.add_field(name="تفاصيل الكلانات", value=clans_info, inline=False)
    
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
