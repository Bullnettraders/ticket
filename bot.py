import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID"))
SUPPORT_ROLE_NAME = os.getenv("SUPPORT_ROLE_NAME")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 🎓 FAQ-Buttons
class TradingFAQButtons(discord.ui.View):
    @discord.ui.button(label="📈 Wie starte ich mit Trading?", style=discord.ButtonStyle.secondary)
    async def start_trading(self, interaction, button):
        await interaction.response.send_message(
            "📈 Starte mit dem **Einsteiger-Guide im #lernbereich** und unserem Einführungskurs.", ephemeral=True)

    @discord.ui.button(label="💰 VIP-Zugang", style=discord.ButtonStyle.secondary)
    async def vip_info(self, interaction, button):
        await interaction.response.send_message(
            "💰 Der VIP-Zugang bietet dir exklusive Signale, Live-Calls & Mentoring. Details in #vip-info.", ephemeral=True)

    @discord.ui.button(label="⏰ Live-Sessions", style=discord.ButtonStyle.secondary)
    async def livesessions(self, interaction, button):
        await interaction.response.send_message(
            "⏰ Live-Sessions sind **Mo–Fr um 18:00 Uhr** in #live-session verfügbar.", ephemeral=True)

    @discord.ui.button(label="📚 Lernmaterialien", style=discord.ButtonStyle.secondary)
    async def lernmaterial(self, interaction, button):
        await interaction.response.send_message(
            "📚 Lernmaterialien, eBooks und Videos findest du in #ressourcen.", ephemeral=True)

# ❌ Ticket schließen
class CloseTicketView(discord.ui.View):
    @discord.ui.button(label="❌ Ticket schließen", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction, button):
        await interaction.response.send_message("🗑️ Ticket wird geschlossen...", ephemeral=True)
        log_channel = discord.utils.get(interaction.guild.text_channels, name="ticket-log")
        if log_channel:
            await log_channel.send(f"📁 Ticket von {interaction.user.mention} wurde geschlossen: `{interaction.channel.name}`")
        await interaction.channel.delete()

# 🎫 Ticket öffnen
class TicketButton(discord.ui.View):
    @discord.ui.button(label="🎫 Ticket eröffnen", style=discord.ButtonStyle.green)
    async def open_ticket(self, interaction, button):
        guild = interaction.guild
        user = interaction.user
        category = discord.utils.get(guild.categories, id=CATEGORY_ID)
        support_role = discord.utils.get(guild.roles, name=SUPPORT_ROLE_NAME)

        if not category or not support_role:
            await interaction.response.send_message("❌ Kategorie oder Rolle nicht gefunden.", ephemeral=True)
            return

        existing = discord.utils.get(category.channels, name=f"ticket-{user.name.lower()}-{user.discriminator}")
        if existing:
            await interaction.response.send_message("Du hast bereits ein offenes Ticket.", ephemeral=True)
            return

        channel_name = f"ticket-{user.name.lower().replace(' ', '-')}-{user.discriminator}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            support_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites, topic=str(user.id))
        await channel.send(f"{support_role.mention} | {user.mention}, willkommen beim Support! Wähle unten oder beschreibe dein Anliegen.", view=TradingFAQButtons())
        await channel.send(view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket erstellt: {channel.mention}", ephemeral=True)

@bot.command()
async def setup(ctx):
    await ctx.send("🎟️ Klicke unten, um ein Ticket zu eröffnen:", view=TicketButton())

@bot.event
async def on_ready():
    print(f"✅ Bot ist online als: {bot.user.name}")

bot.run(TOKEN)
