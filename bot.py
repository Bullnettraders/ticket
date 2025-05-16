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

    @discord.ui.button(label="💳 Zahlungsfragen", style=discord.ButtonStyle.secondary)
    async def billing_help(self, interaction, button):
        await interaction.response.send_message(
            "💬 Für Rechnungen, Abos oder Rückerstattungen – gib bitte deinen Kaufnachweis an. "
            "Unser Finanzteam meldet sich!", ephemeral=True)

    @discord.ui.button(label="🧠 Allgemeine Frage", style=discord.ButtonStyle.secondary)
    async def general_question(self, interaction, button):
        await interaction.response.send_message(
            "❓ Stelle deine Frage hier im Ticket – unser Team hilft dir so schnell wie möglich.", ephemeral=True)

# ❌ Ticket schließen
class CloseTicketView(discord.ui.View):
    @discord.ui.button(label="❌ Ticket schließen", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction, button):
        await interaction.response.send_message("🗑️ Ticket wird geschlossen...", ephemeral=True)
        log_channel = discord.utils.get(interaction.guild.text_channels, name="ticket-log")
        if log_channel:
            await log_channel.send(f"📁 Ticket von {interaction.user.mention} wurde geschlossen: `{interaction.channel.name}`")
        await interaction.channel.delete()

# 🎫 Ticket eröffnen
class TicketButton(discord.ui.View):
    @discord.ui.button(label="🎫 Support-Ticket eröffnen", style=discord.ButtonStyle.green)
    async def open_ticket(self, interaction, button):
        guild = interaction.guild
        user = interaction.user
        category = discord.utils.get(guild.categories, id=CATEGORY_ID)
        support_role = discord.utils.get(guild.roles, name=SUPPORT_ROLE_NAME)

        if not category or not support_role:
            await interaction.response.send_message("❌ Kategorie oder Support-Rolle nicht gefunden.", ephemeral=True)
            return

        channel_name = f"ticket-{user.name.lower().replace(' ', '-')}-{user.discriminator}"
        for c in category.channels:
            if c.name == channel_name:
                await interaction.response.send_message("⚠️ Du hast bereits ein offenes Ticket.", ephemeral=True)
                return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            support_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites, topic=str(user.id))
        await channel.send(f"{support_role.mention} | {user.mention}, willkommen beim Support! Bitte wähle unten oder beschreibe dein Anliegen.", view=TradingFAQButtons())
        await channel.send(view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket erstellt: {channel.mention}", ephemeral=True)

# 🟢 Automatisch Button posten beim Start
@bot.event
async def on_ready():
    print(f"✅ Bot ist online als: {bot.user.name}")
    channel = bot.get_channel(TICKET_CHANNEL_ID)
    if channel:
        await channel.send("🎟️ Brauchst du Hilfe? Klicke auf den Button:", view=TicketButton())

bot.run(TOKEN)
