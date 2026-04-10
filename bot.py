import discord
from discord import app_commands
import os
from dotenv import load_dotenv
from db import init_db, log_task, get_last_tasks

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))

MAIN_CHANNEL_ID = int(os.getenv("JARVIS_MAIN_CHANNEL_ID"))
ALERTS_CHANNEL_ID = int(os.getenv("JARVIS_ALERTS_CHANNEL_ID"))
OPS_CHANNEL_ID = int(os.getenv("JARVIS_OPS_CHANNEL_ID"))

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await init_db()
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

client = MyClient()

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.tree.command(name="ping", description="Check if bot is alive")
async def ping(interaction: discord.Interaction):
    await log_task("ping", str(interaction.user.id), str(interaction.channel_id))
    await interaction.response.send_message("pong 🏓")

@client.tree.command(name="status", description="Check system status")
async def status(interaction: discord.Interaction):
    await log_task("status", str(interaction.user.id), str(interaction.channel_id))
    await interaction.response.send_message("Jarvis online")

@client.tree.command(name="say", description="Send test messages to jarvis-main")
async def say(interaction: discord.Interaction):
    await log_task("say", str(interaction.user.id), str(interaction.channel_id))
    main_channel = client.get_channel(MAIN_CHANNEL_ID)

    if main_channel:
        await main_channel.send("Message to #jarvis-main")

    await interaction.response.send_message("Message sent to #jarvis-main ✅", ephemeral=True)

@client.tree.command(name="tasks", description="Show last 5 commands")
async def tasks(interaction: discord.Interaction):
    rows = await get_last_tasks(5)

    if not rows:
        await interaction.response.send_message("No tasks logged yet.")
        return

    lines = []
    for row in rows:
        task_id, command, user_id, channel_id, created_at = row
        lines.append(f"{task_id}. /{command} | user:{user_id} | channel:{channel_id} | {created_at}")

    message = "\n".join(lines)
    await interaction.response.send_message(f"Last tasks:\n{message}")

client.run(TOKEN)
