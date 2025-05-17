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

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.name.startswith("ticket-"):
        content = message.content.lower()

        # Allgemeine Fragen
        keywords_allgemein = ["trading starten", "regeln", "lernbereich", "tutorial", "vorstellen", "live-session", "mentor", "feedback"]
        if any(word in content for word in keywords_allgemein):
            await message.channel.send(
                "💡 **Allgemeine Infos:**\n"
                "- Starte mit unserem Einsteiger-Guide im #lernbereich.\n"
                "- Die Community-Regeln findest du im Channel #regeln.\n"
                "- Es gibt regelmäßige Live-Trading-Sessions Mo-Fr um 18 Uhr.\n"
                "- Kontaktiere Mentoren über den Support oder im #mentor-chat.\n"
                "- Feedback und Vorschläge sind im Channel #feedback willkommen.",
                delete_after=60)
            return

        # Indikator-Fragen
        keywords_indikatoren = ["indikator", "indikatoren", "tradingview", "funktion", "erklärung", "was können die indikator"]
        if any(word in content for word in keywords_indikatoren):
            await message.channel.send(
                "**Unsere Indikatoren im Überblick:**\n"
                "- **HELD:** Erkennung von starken Trends und Einstiegen.\n"
                "- **ESXY:** Volatilitäts- und Momentum-Analyse.\n"
                "- **COMO:** Vielseitige Marktanalyse und Signale.\n"
                "- **GAPA:** Fokus auf Breakouts und Kurslücken.\n"
                "- **DESC:** Detailanalyse von Kursbewegungen.\n"
                "- **BAS:** Bullnet Strategie mit ca. 80% Trefferquote.\n"
                "- **GABO:** Kombinierte Signale für präzise Einstiege.",
                delete_after=60)
            return

        # Pakete & Preise
        keywords_pakete = ["paket", "preise", "classic", "pro", "elite", "unterschied", "upgrade"]
        if any(word in content for word in keywords_pakete):
            await message.channel.send(
                "**Unsere Pakete:**\n"
                "- Classic: kostenlos\n"
                "- Pro: ab 89 Euro, inkl. 5 Indikatoren, Schulungsbereich, News, Live-Calls\n"
                "- Elite: ab 299 Euro, alle Indikatoren, Bullnet Strategie mit BAS Indikator, voller Discord-Zugang\n"
                "Zum Upgrade und Buchung: https://whop.com/bullnet-pro-ad/?a=bullnetinfo",
                delete_after=60)
            return

        # Whop & Zahlung
        keywords_whop = ["whop", "zahlung", "abo", "kündigen", "geld zurück", "shop"]
        if any(word in content for word in keywords_whop):
            await message.channel.send(
                "💳 **Zahlungen und Whop:**\n"
                "- Zahlungen laufen über Whop.com.\n"
                "- Du kannst dein Abo jederzeit kündigen.\n"
                "- Geld-zurück-Garantie je nach Paketbedingungen.\n"
                "- Shop-Link: https://whop.com/bullnet-pro-ad/?a=bullnetinfo",
                delete_after=60)
            return

        # Technik & Zugriffsfragen
        keywords_technik = ["channel sehen", "rolle", "discord verbinden", "zugriff", "benachrichtigung", "stumm"]
        if any(word in content for word in keywords_technik):
            await message.channel.send(
                "🔧 **Technik & Zugriff:**\n"
                "- Du brauchst mindestens das Pro-Paket für Zugriff auf alle Channels.\n"
                "- Verknüpfe deinen Discord Account auf Whop.com im Profil.\n"
                "- Falls du keine Rolle hast, melde dich im Support.\n"
                "- Benachrichtigungen kannst du per Rechtsklick auf den Channel stumm schalten.",
                delete_after=60)
            return

    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"✅ Bot ist online als: {bot.user.name}")
    channel = bot.get_channel(TICKET_CHANNEL_ID)
    if channel:
        await channel.send("🎟️ Brauchst du Hilfe? Klicke hier, um ein Ticket zu eröffnen:", view=TicketButton())

bot.run(TOKEN)
