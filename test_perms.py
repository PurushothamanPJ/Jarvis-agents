import asyncio
import os
import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
MAIN_CHANNEL_ID = int(os.getenv("JARVIS_MAIN_CHANNEL_ID"))

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user}')
        channel = self.get_channel(MAIN_CHANNEL_ID)
        try:
            msg = await channel.send("Test message from Py")
            print("Successfully sent message to MAIN_CHANNEL")
            await msg.delete()
        except Exception as e:
            print(f"Error sending to MAIN channel: {e}")
            
        await self.close()

client = MyClient(intents=discord.Intents.default())
client.run(TOKEN)
