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
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Ticket schließen View
class CloseTicketView(discord.ui.View):
    @discord.ui.button(label="❌ Ticket schließen", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🗑️ Ticket wird geschlossen...", ephemeral=True)
        try:
            await interaction.channel.delete()
        except Exception as e:
            await interaction.followup.send(f"Fehler beim Löschen des Tickets: {e}", ephemeral=True)

# Ticket öffnen Button
class TicketButton(discord.ui.View):
    @discord.ui.button(label="🎫 Support-Ticket eröffnen", style=discord.ButtonStyle.green)
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        category = discord.utils.get(guild.categories, id=CATEGORY_ID)

        if SUPPORT_ROLE_NAME.isdigit():
            support_role = guild.get_role(int(SUPPORT_ROLE_NAME))
        else:
            support_role = discord.utils.get(guild.roles, name=SUPPORT_ROLE_NAME)

        if not category:
            await interaction.response.send_message("❌ Ticket-Kategorie nicht gefunden!", ephemeral=True)
            return
        if not support_role:
            await interaction.response.send_message("❌ Support-Rolle nicht gefunden!", ephemeral=True)
            return

        channel_name = f"ticket-{user.name.lower().replace(' ', '-')}-{user.discriminator}"
        existing = discord.utils.get(category.channels, name=channel_name)
        if existing:
            await interaction.response.send_message("⚠️ Du hast bereits ein offenes Ticket.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            support_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        ticket_channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        await ticket_channel.send(f"{support_role.mention} | {user.mention}, willkommen beim Support! Schreibe hier dein Anliegen.", view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket erstellt: {ticket_channel.mention}", ephemeral=True)

# Keyword-Erkennung für automatische Antworten
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.name.startswith("ticket-"):
        content = message.content.lower()

        keywords_upgrade = ["upgrade", "pro paket", "kanäle sehen", "channels sehen", "zugriff"]
        keywords_link_upgrade = ["link upgrade", "upgrade link", "upgrade"]
        keywords_indikatoren = ["indikator", "indikatoren", "tradingview", "trading"]
        keywords_preise = ["preis", "preise", "kosten"]
        keywords_erwerbbar = ["erwerbbar", "kaufen", "shop", "erhalten"]

        if any(word in content for word in keywords_upgrade):
            await message.channel.send(
                "🔒 Du benötigst mindestens das Pro-Paket, um Zugriff auf diese Channels zu erhalten. "
                "Hier kannst du upgraden: https://whop.com/pro-upgrade",
                delete_after=20)

        elif any(word in content for word in keywords_link_upgrade):
            await message.channel.send(
                "🔗 Hier findest du den Link zum Whop Pro Upgrade: https://whop.com/pro-upgrade",
                delete_after=20)

        elif any(word in content for word in keywords_indikatoren):
            await message.channel.send(
                "📊 Die Indikatoren findest du hier: https://whop.com/marketplace/trading-indicators/",
                delete_after=20)

        elif any(word in content for word in keywords_preise):
            await message.channel.send(
                "💰 Die Preise variieren je nach Indikator. Mehr Infos hier: https://whop.com/marketplace/trading-indicators/",
                delete_after=20)

        elif any(word in content for word in keywords_erwerbbar):
            await message.channel.send(
                "🛒 Verfügbare Indikatoren findest du im Whop Marketplace: https://whop.com/marketplace/trading-indicators/",
                delete_after=20)

    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"✅ Bot ist online als: {bot.user.name}")
    channel = bot.get_channel(TICKET_CHANNEL_ID)
    if channel:
        await channel.send("🎟️ Brauchst du Hilfe? Klicke hier, um ein Ticket zu eröffnen:", view=TicketButton())

bot.run(TOKEN)
