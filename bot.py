import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

# 🔐 .env laden
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID"))
TICKET_CHANNEL_ID = int(os.getenv("TICKET_CHANNEL_ID"))
SUPPORT_ROLE_NAME = os.getenv("SUPPORT_ROLE_NAME")

# ✅ Discord Intents aktivieren
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 📚 FAQ-Buttons
class TradingFAQButtons(discord.ui.View):
    @discord.ui.button(label="🔐 Whop-Zugang funktioniert nicht", style=discord.ButtonStyle.secondary)
    async def whop_help(self, interaction, button):
        await interaction.response.send_message(
            "📌 Stelle sicher, dass dein Discord-Account korrekt mit Whop verknüpft ist. "
            "Gib bei Problemen bitte deine Bestellnummer oder E-Mail an.", ephemeral=True)

    @discord.ui.button(label="📈 Indikator wird nicht angezeigt", style=discord.ButtonStyle.secondary)
    async def indikator_help(self, interaction, button):
        await interaction.response.send_message(
            "📊 Folge bitte der Anleitung in #setup-indikator. Falls es nicht klappt, helfen wir dir hier weiter.", ephemeral=True)

    @discord.ui.button(label="💳 Zahlungsfragen", style=discord.ButtonStyle.secondary)
    async def payment_help(self, interaction, button):
        await interaction.response.send_message(
            "💳 Für Zahlungsfragen nenne uns bitte deine Whop-Bestellnummer. Unser Team meldet sich bald!", ephemeral=True)

    @discord.ui.button(label="💬 Allgemeine Frage", style=discord.ButtonStyle.secondary)
    async def general_help(self, interaction, button):
        await interaction.response.send_message(
            "💬 Stelle deine Frage hier – unser Team antwortet schnellstmöglich.", ephemeral=True)

# ❌ Ticket schließen
class CloseTicketView(discord.ui.View):
    @discord.ui.button(label="❌ Ticket schließen", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction, button):
        await interaction.response.send_message("🗑️ Ticket wird geschlossen...", ephemeral=True)
        log_channel = discord.utils.get(interaction.guild.text_channels, name="ticket-log")
        if log_channel:
            await log_channel.send(f"📁 Ticket von {interaction.user.mention} wurde geschlossen: `{interaction.channel.name}`")
        await interaction.channel.delete()

# 🎫 Ticket erstellen
class TicketButton(discord.ui.View):
    @discord.ui.button(label="🎫 Support-Ticket eröffnen", style=discord.ButtonStyle.green)
    async def open_ticket(self, interaction, button):
        guild = interaction.guild
        user = interaction.user
        category = discord.utils.get(guild.categories, id=CATEGORY_ID)
        support_role = discord.utils.get(guild.roles, name=SUPPORT_ROLE_NAME)

        # 🔍 Debug-Ausgabe
        print(f"[DEBUG] Gesuchter Rollenname: {SUPPORT_ROLE_NAME}")
        print(f"[DEBUG] Gefundene Rolle: {support_role}")
        print(f"[DEBUG] Kategorie-ID: {CATEGORY_ID} | Gefunden: {category}")

        if not category or not support_role:
            await interaction.response.send_message("❌ Kategorie oder Support-Rolle nicht gefunden.", ephemeral=True)
            return

        channel_name = f"ticket-{user.name.lower().replace(' ', '-')}-{user.discriminator}"
        existing_channel = discord.utils.get(category.channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message("⚠️ Du hast bereits ein offenes Ticket.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            support_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        ticket_channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites, topic=str(user.id))
        await ticket_channel.send(
            f"{support_role.mention} | {user.mention}, willkommen beim Support! Wähle unten dein Anliegen oder schreibe es direkt.",
            view=TradingFAQButtons()
        )
        await ticket_channel.send(view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket erstellt: {ticket_channel.mention}", ephemeral=True)

# 🚀 Automatisch Support-Button posten
@bot.event
async def on_ready():
    print(f"✅ Bot ist online als: {bot.user.name}")
    channel = bot.get_channel(TICKET_CHANNEL_ID)
    if channel:
        await channel.send("🎟️ Brauchst du Hilfe? Klicke auf den Button:", view=TicketButton())

bot.run(TOKEN)
