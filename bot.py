import discord
from discord import app_commands
import os
import asyncio
from dotenv import load_dotenv
from db import init_db, create_task, complete_task, get_last_tasks
from router import route_command
from research_agent import run_research

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

@client.tree.command(name="say", description="Send a message to a specific channel")
@app_commands.describe(message="The message to send", target="The channel to send the message to")
async def say(interaction: discord.Interaction, message: str, target: discord.TextChannel):
    await interaction.response.defer(ephemeral=True)
    agent = route_command("say")
    task_id = await create_task("say", str(interaction.user.id), str(interaction.channel_id), agent)
    
    try:
        await target.send(message)
        await interaction.followup.send(f"Message sent to {target.mention} ✅", ephemeral=True)
        await complete_task(task_id, f"Message sent to #{target.name}")
    except discord.Forbidden:
        await interaction.followup.send(f"❌ I don't have permission to send messages in {target.mention}.", ephemeral=True)
        await complete_task(task_id, f"Failed: Missing permission for #{target.name}")

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


@client.tree.command(name="research", description="Run a research query using the Research Agent")
@app_commands.describe(query="What do you want to research?")
async def research(interaction: discord.Interaction, query: str):
    await interaction.response.defer()

    # Use client.get_channel() — gives fully cached TextChannel object with proper access.
    # interaction.channel can be PartialMessageable in slash commands (no real permissions).
    channel = client.get_channel(interaction.channel_id)
    if channel is None:
        # Not in cache — fetch directly from Discord API
        channel = await client.fetch_channel(interaction.channel_id)

    thread_name = f"Research: {query[:80]}"
    thread = None
    thread_id = None

    # Try to create a public thread from the proper channel object
    try:
        thread = await channel.create_thread(
            name=thread_name,
            type=discord.ChannelType.public_thread
        )
        thread_id = str(thread.id)

        await interaction.followup.send(
            f"🔍 Research task received for: **{query}**\n"
            f"⤵️ Head to {thread.mention} for live updates."
        )
    except discord.Forbidden:
        # Fallback: post everything directly in the channel
        await interaction.followup.send(
            f"🔍 Research task received for: **{query}**\n"
            f"⚠️ *Thread creation failed. Posting updates here instead.*"
        )

    # Helper to send messages to thread if available, else fallback to followup
    async def post_update(content: str):
        if thread:
            await thread.send(content)
        else:
            await interaction.followup.send(content)

    # Log task to DB
    agent = route_command("research")
    task_id = await create_task(
        "research",
        str(interaction.user.id),
        str(interaction.channel_id),
        agent,
        thread_id=thread_id
    )

    # Post progress updates
    await post_update("🔎 Research agent started...")
    await asyncio.sleep(1)
    await post_update(f"📋 Working on query: **{query}**")

    # Run the research agent
    result = await run_research(query)

    # Post final result
    await post_update(result)

    # Mark task completed in DB
    await complete_task(task_id, "Research completed")


client.run(TOKEN)
