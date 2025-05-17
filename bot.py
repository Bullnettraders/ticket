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

# Ticket schließen View mit Fehlerbehandlung
class CloseTicketView(discord.ui.View):
    @discord.ui.button(label="❌ Ticket schließen", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🗑️ Ticket wird geschlossen...", ephemeral=True)
        try:
            await interaction.channel.delete()
        except discord.Forbidden:
            await interaction.followup.send("❌ Ich habe keine Rechte, um diesen Channel zu löschen. Bitte überprüfe meine Berechtigungen.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.followup.send(f"❌ Fehler beim Löschen des Channels: {e}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Unerwarteter Fehler: {e}", ephemeral=True)

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
        keywords_einzeln = ["einzeln buchen", "einzelner indikator", "preis indikator", "preis je indikator"]
        keywords_classic_pro = ["unterschied classic pro", "classic vs pro", "was ist pro"]
        keywords_pro_elite = ["unterschied pro elite", "pro vs elite", "was ist elite"]

        if any(word in content for word in keywords_upgrade):
            await message.channel.send(
                "🔒 Du benötigst mindestens das Pro-Paket, um Zugriff auf diese Channels zu erhalten. "
                "Hier kannst du upgraden: https://whop.com/pro-upgrade",
                delete_after=30)

        elif any(word in content for word in keywords_link_upgrade):
            await message.channel.send(
                "🔗 Hier findest du den Link zum Whop Pro Upgrade: https://whop.com/pro-upgrade",
                delete_after=30)

        elif any(word in content for word in keywords_indikatoren):
            await message.channel.send(
                "📈 Um die Indikatoren in TradingView zu finden, klicke links auf 'Indikatoren' und dann im Bereich 'Invite-only' findest du unsere exklusiven Skripte.\n"
                "👉 Hier geht’s zum Whop-Shop: https://whop.com/bullnet-pro-ad/?a=bullnetinfo",
                delete_after=40)

        elif any(word in content for word in keywords_preise):
            await message.channel.send(
                "💼 Unsere Pakete und Preise:\n"
                "• Classic – kostenlos\n"
                "• Pro – ab 89 Euro, inklusive 5 Indikatoren\n"
                "• Elite – ab 299 Euro, inklusive alle Indikatoren plus den BAS Indikator",
                delete_after=40)

        elif any(word in content for word in keywords_einzeln):
            await message.channel.send(
                "💡 Du kannst die Indikatoren auch einzeln buchen. Preis je Indikator: 24,99 € zzgl. MwSt.\n"
                "👉 Hier zum Einzelkauf: https://whop.com/bullnet-pro-ad/?a=bullnetinfo",
                delete_after=40)

        elif any(word in content for word in keywords_classic_pro):
            await message.channel.send(
                "ℹ️ Unterschied Classic und Pro:\n"
                "Classic ist kostenlos und bietet Grundfunktionen.\n"
                "Pro enthält zusätzlich den kompletten Schulungsbereich, News und Live-Calls.",
                delete_after=40)

        elif any(word in content for word in keywords_pro_elite):
            await message.channel.send(
                "🔥 Unterschied Pro und Elite:\n"
                "Elite bietet vollen Zugriff inklusive Discord und der Bullnet Strategie mit dem BAS Indikator, "
                "der eine Trefferquote von 80% hat.",
                delete_after=40)

    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"✅ Bot ist online als: {bot.user.name}")
    channel = bot.get_channel(TICKET_CHANNEL_ID)
    if channel:
        await channel.send("🎟️ Brauchst du Hilfe? Klicke hier, um ein Ticket zu eröffnen:", view=TicketButton())

bot.run(TOKEN)
