import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID"))
SUPPORT_ROLE_NAME = os.getenv("SUPPORT_ROLE_NAME")
TICKET_CHANNEL_ID = int(os.getenv("TICKET_CHANNEL_ID"))

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# FAQ für Whop-Nutzer
class TradingFAQButtons(discord.ui.View):
    @discord.ui.button(label="🔐 Whop-Zugang funktioniert nicht", style=discord.ButtonStyle.secondary)
    async def whop_help(self, interaction, button):
        await interaction.response.send_message(
            "📌 Stelle sicher, dass du bei Whop **den gleichen Discord-Account** verknüpft hast. "
            "Falls dein Zugang nicht funktioniert, sende uns bitte deine **Bestellnummer** oder **E-Mail**.", ephemeral=True)

    @discord.ui.button(label="📈 Indikator wird nicht angezeigt", style=discord.ButtonStyle.secondary)
    async def indicator_help(self, interaction, button):
        await interaction.response.send_message(
            "📊 Stelle sicher, dass du den Indikator korrekt installiert hast (Anleitung findest du in #setup-indikator). "
            "Falls das nicht hilft, helfen wir dir gleich weiter.", ephemeral=True)

    @discord.ui.
