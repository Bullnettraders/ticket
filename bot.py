import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID"))
TICKET_CHANNEL_ID = int(os.getenv("TICKET_CHANNEL_ID"))
SUPPORT_ROLE_NAME = os.getenv("SUPPORT_ROLE_NAME")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

class CloseTicketView(discord.ui.View):
    @discord.ui.button(label="❌ Ticket schließen", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🗑️ Ticket wird geschlossen...", ephemeral=True)
        try:
            await interaction.channel.delete()
        except Exception as e:
            await interaction.followup.send(f"Fehler beim Löschen des Tickets: {e}", ephemeral=True)

class TicketButton(discord.ui.View):
    @discord.ui.button(label="🎫 Support-Ticket eröffnen", style=discord.ButtonStyle.green)
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        print(f"[DEBUG] Guild: {guild}, User: {user}")

        category = discord.utils.get(guild.categories, id=CATEGORY_ID)
        print(f"[DEBUG] Gefundene Kategorie: {category}")

        if not category:
            await interaction.response.send_message("❌ Ticket-Kategorie nicht gefunden!", ephemeral=True)
            return

        if SUPPORT_ROLE_NAME.isdigit():
            support_role = guild.get_role(int(SUPPORT_ROLE_NAME))
        else:
            support_role = discord.utils.get(guild.roles, name=SUPPORT_ROLE_NAME)
        print(f"[DEBUG] Support-Rolle: {support_role}")

        if not support_role:
            await interaction.response.send_message("❌ Support-Rolle nicht gefunden!", ephemeral=True)
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

        try:
            ticket_channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites, topic=str(user.id))
            await ticket_channel.send(f"{support_role.mention} | {user.mention}, willkommen beim Support!", view=CloseTicketView())
            await interaction.response.send_message(f"✅ Ticket erstellt: {ticket_channel.mention}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Fehler beim Erstellen des Tickets: {e}", ephemeral=True)
            print(f"[ERROR] Fehler beim Erstellen des Tickets: {e}")

@bot.event
async def on_ready():
    print(f"✅ Bot ist online als: {bot.user.name}")
    channel = bot.get_channel(TICKET_CHANNEL_ID)
    if channel:
        await channel.send("🎟️ Brauchst du Hilfe? Klicke hier, um ein Ticket zu eröffnen:", view=TicketButton())

@bot.event
async def on_message(message):
    # Ignoriere Bot-Nachrichten
    if message.author.bot:
        return

    # Prüfe, ob es ein Ticket-Channel ist (z.B. Name beginnt mit "ticket-")
    if message.channel.name.startswith("ticket-"):
        content = message.content.lower()

        # Beispiel-Schlüsselwörter und passende Antworten
        if "lizenz" in content or "license" in content:
            await message.channel.send(
                "🔑 Du suchst deine Lizenz? Schau in deinem Whop-Dashboard unter Orders → View.",
                delete_after=20)
        elif "zahlung" in content or "pay" in content or "rechn" in content:
            await message.channel.send(
                "💳 Zahlungsfragen? Bitte wende dich an support@whop.com oder prüfe deine Zahlungsdetails bei Whop.",
                delete_after=20)
        elif "discord verbinden" in content or "connect" in content:
            await message.channel.send(
                "🔗 So verknüpfst du Discord mit Whop:\n1. Gehe zu https://whop.com\n2. Klicke auf dein Profil → Connect Discord",
                delete_after=20)
        elif "indikator" in content or "indicator" in content:
            await message.channel.send(
                "📊 Für den Indikator in TradingView:\nKlicke in TradingView auf Indikatoren → Invite-only Scripts.",
                delete_after=20)
        # Füge gerne mehr Schlüsselwörter hinzu!

    # Wichtig: sonst keine Commands blockieren
    await bot.process_commands(message)


bot.run(TOKEN)
