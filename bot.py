import discord
from discord.ext import commands
import openai
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)
openai.api_key = os.getenv("OPENAI_API_KEY")
GUILD_ID = int(os.getenv("GUILD_ID"))
SUPPORT_ROLE_ID = int(os.getenv("SUPPORT_ROLE_ID"))
CATEGORY_ID = int(os.getenv("CATEGORY_ID"))

@bot.event
async def on_ready():
    print(f"Bot ist online als {bot.user}")

@bot.command()
async def ticket(ctx, *, grund: str):
    guild = ctx.guild
    category = discord.utils.get(guild.categories, id=CATEGORY_ID)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.get_role(SUPPORT_ROLE_ID): discord.PermissionOverwrite(read_messages=True)
    }
    channel = await guild.create_text_channel(name=f"ticket-{ctx.author.name}", category=category, overwrites=overwrites)
    await channel.send(f"Hallo {ctx.author.mention}, dein Ticket wurde erstellt. Bitte beschreibe dein Problem.")
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Du bist ein hilfsbereiter Support-Bot."},
            {"role": "user", "content": grund}
        ]
    )
    await channel.send(f"AI: {response.choices[0].message.content}")
    await ctx.send(f"Ticket wurde erstellt: {channel.mention}")

@bot.command()
async def close(ctx):
    if ctx.channel.name.startswith("ticket-"):
        await ctx.send("Ticket wird geschlossen...")
        await ctx.channel.delete()

bot.run(os.getenv("DISCORD_TOKEN"))
