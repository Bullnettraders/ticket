import discord
from discord.ext import commands
from discord import Interaction, ButtonStyle
from discord.ui import Button, View
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
SUPPORT_CHANNEL_ID = int(os.getenv("SUPPORT_CHANNEL_ID"))

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ticket erstellen", style=ButtonStyle.green, custom_id="create_ticket")
    async def create_ticket(self, interaction: Interaction, button: Button):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, id=CATEGORY_ID)
        existing = discord.utils.get(guild.text_channels, name=f"ticket-{interaction.user.name.lower()}")

        if existing:
            await interaction.response.send_message(f"Du hast bereits ein offenes Ticket: {existing.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.get_role(SUPPORT_ROLE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(f"ticket-{interaction.user.name}", category=category, overwrites=overwrites)

        await channel.send(f"Hallo {interaction.user.mention}, willkommen im Support. Bitte schildere dein Problem.")

        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein hilfsbereiter Support-Bot."},
                {"role": "user", "content": "Der Benutzer hat soeben ein Ticket eröffnet, bitte gib eine erste Begrüßung."}
            ]
        )
        await channel.send(f"AI: {response.choices[0].message.content}")

        await interaction.response.send_message(f"Dein Ticket wurde erstellt: {channel.mention}", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Bot ist online als {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Slash Commands synchronisiert: {len(synced)}")
    except Exception as e:
        print(e)

    # Automatisch Ticket-Panel senden
    channel = bot.get_channel(SUPPORT_CHANNEL_ID)
    if channel:
        view = TicketView()
        await channel.send("**Brauchst du Hilfe?**\nKlicke auf den Button, um ein Support-Ticket zu erstellen.", view=view)

bot.run(os.getenv("DISCORD_TOKEN"))
