import discord
from discord import app_commands
import os
from dotenv import load_dotenv
from db import init_db, create_task, complete_task, get_last_tasks
from router import route_command

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
    # Defer immediately — prevents Unknown Interaction (10062) error
    await interaction.response.defer()
    agent = route_command("ping")
    task_id = await create_task("ping", str(interaction.user.id), str(interaction.channel_id), agent)
    await interaction.followup.send("pong 🏓")
    await complete_task(task_id, "Pong sent")

@client.tree.command(name="status", description="Check system status")
async def status(interaction: discord.Interaction):
    await interaction.response.defer()
    agent = route_command("status")
    task_id = await create_task("status", str(interaction.user.id), str(interaction.channel_id), agent)
    await interaction.followup.send("Jarvis online ✅")
    await complete_task(task_id, "Status checked")

@client.tree.command(name="say", description="Send test messages to jarvis-main")
async def say(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    agent = route_command("say")
    task_id = await create_task("say", str(interaction.user.id), str(interaction.channel_id), agent)
    main_channel = client.get_channel(MAIN_CHANNEL_ID)
    if main_channel:
        await main_channel.send("Message to #jarvis-main")
    await interaction.followup.send("Message sent to #jarvis-main ✅", ephemeral=True)
    await complete_task(task_id, "Message sent to jarvis-main")

@client.tree.command(name="tasks", description="Show last 5 commands")
async def tasks(interaction: discord.Interaction):
    await interaction.response.defer()
    # Fetch rows FIRST — before logging this command — so /tasks doesn't show itself as 'received'
    rows = await get_last_tasks(5)
    agent = route_command("tasks")
    task_id = await create_task("tasks", str(interaction.user.id), str(interaction.channel_id), agent)

    if not rows:
        await interaction.followup.send("No tasks logged yet.")
        await complete_task(task_id, "No tasks found")
        return

    lines = []
    for row in rows:
        task_id_db, command, user_id, channel_id, created_at, task_status, agent_db, result = row
        lines.append(f"{task_id_db}. /{command} | {task_status} | {agent_db} | {created_at}")

    message = "\n".join(lines)
    await interaction.followup.send(f"Last tasks:\n{message}")
    await complete_task(task_id, f"Displayed {len(rows)} tasks")

client.run(TOKEN)
