import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

# Lädt lokale .env (lokal nutzbar, ignoriert, wenn keine .env da)
load_dotenv()

# Environment-Variablen (Railway setzt die automatisch)
TOKEN = os.getenv("DISCORD_TOKEN")
CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID"))
TICKET_CHANNEL_ID = int(os.getenv("TICKET_CHANNEL_ID"))
SUPPORT_ROLE_NAME = os.getenv("SUPPORT_ROLE_NAME")
WHOP_LINK = os.getenv("WHOP_LINK") or "https://whop.com/bullnet-pro-ad/?a=bullnetinfo"

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

class WhopFAQDropdown(discord.ui.View):
    @discord.ui.select(
        placeholder="Wähle ein Thema zu Whop...",
        options=[
            discord.SelectOption(label="Discord verbinden", description="Wie verbinde ich meinen Discord Account"),
            discord.SelectOption(label="Lizenz finden", description="Wo finde ich meine Lizenz"),
            discord.SelectOption(label="Keine Kanäle sichtbar", description="Probleme mit Discord-Rollen"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        choice = select.values[0]
        if choice == "Discord verbinden":
            await interaction.response.send_message(
                "🔗 So verbindest du deinen Discord:\n"
                "1. Gehe auf https://whop.com\n"
                "2. Melde dich an\n"
                "3. Klicke oben rechts auf dein Profil → **Connect Discord**\n"
                "4. Folge den Anweisungen, danach wirst du eingeladen.",
                ephemeral=True)
        elif choice == "Lizenz finden":
            await interaction.response.send_message(
                "🧾 Deine Lizenz findest du unter https://whop.com → Profil → **Orders** → **View**.",
                ephemeral=True)
        elif choice == "Keine Kanäle sichtbar":
            await interaction.response.send_message(
                "🚫 Prüfe:\n- Discord mit Whop verknüpft?\n- Rolle erhalten?\n- Weniger als 100 Server?\n- Discord neu starten.",
                ephemeral=True)

class TicketFAQButtons(discord.ui.View):
    @discord.ui.button(label="Whop FAQ", style=discord.ButtonStyle.primary)
    async def whop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Bitte wähle ein Thema aus:", view=WhopFAQDropdown(), ephemeral=True)

class ExtraInfoButtons(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(label="🔗 Whop-Shop", style=discord.ButtonStyle.link, url=WHOP_LINK))

    @discord.ui.button(label="📊 Indikator-Infos", style=discord.ButtonStyle.secondary)
    async def indicator_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "📊 Unsere Indikatoren findest du in TradingView unter „Invite-only Scripts“. "
            "Falls du Hilfe brauchst, melde dich hier.", ephemeral=True)

    @discord.ui.button(label="🔇 Anleitung: Mute einstellen", style=discord.ButtonStyle.secondary)
    async def mute_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🔇 Um Benachrichtigungen stummzuschalten:\n"
            "- Rechtsklick auf den Channel → Benachrichtigungen → Stumm\n"
            "- Oder nutze die Server-Stummschaltung oben links.", ephemeral=True)

class CloseTicketView(discord.ui.View):
    @discord.ui.button(label="❌ Ticket schließen", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🗑️ Ticket wird geschlossen...", ephemeral=True)
        log_channel = discord.utils.get(interaction.guild.text_channels, name="ticket-log")
        if log_channel:
            await log_channel.send(f"📁 Ticket von {interaction.user.mention} wurde geschlossen: `{interaction.channel.name}`")
        try:
            await interaction.channel.delete()
        except Exception as e:
            await interaction.followup.send(f"Fehler beim Löschen des Tickets: {e}", ephemeral=True)

class TicketButton(discord.ui.View):
    @discord.ui.button(label="🎫 Support-Ticket eröffnen", style=discord.ButtonStyle.green)
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        category = discord.utils.get(guild.categories, id=CATEGORY_ID)
        support_role = guild.get_role(int(SUPPORT_ROLE_NAME)) if SUPPORT_ROLE_NAME.isdigit() else discord.utils.get(guild.roles, name=SUPPORT_ROLE_NAME)

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
        await ticket_channel.send(f"{support_role.mention} | {user.mention}, willkommen beim Support! Nutze den Whop FAQ Button unten oder schreibe dein Anliegen.", view=TicketFAQButtons())
        await ticket_channel.send(view=ExtraInfoButtons())
        await ticket_channel.send(view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket erstellt: {ticket_channel.mention}", ephemeral=True)

@bot.event
async def on_ready():
    print(f"✅ Bot ist online als: {bot.user.name}")
    channel = bot.get_channel(TICKET_CHANNEL_ID)
    if channel:
        await channel.send("🎟️ Brauchst du Hilfe? Klicke unten auf den Button:", view=TicketButton())

bot.run(TOKEN)
