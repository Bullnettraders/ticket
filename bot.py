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
        await interaction.response.defer(ephemeral=True)
        try:
            await interaction.channel.delete()
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Ich habe keine Berechtigung, diesen Channel zu löschen. Bitte gib mir die Rechte „Kanäle verwalten“.",
                ephemeral=True)
        except discord.HTTPException as e:
            await interaction.followup.send(f"❌ Fehler beim Löschen: {e}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Unerwarteter Fehler: {e}", ephemeral=True)

class SupportConfirmView(discord.ui.View):
    def __init__(self, support_role):
        super().__init__(timeout=120)
        self.support_role = support_role

    @discord.ui.button(label="Ja, Support-Team kontaktieren", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"{self.support_role.mention} | {interaction.user.mention} braucht Unterstützung!", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Nein, danke", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Okay, wie kann ich dir sonst noch helfen?", ephemeral=True)
        self.stop()

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

        # Kurze Begrüßung
        await ticket_channel.send(
            f"Hallo {user.mention}, du schreibst mit Kalle! Ich beantworte viele Fragen automatisch. "
            "Wenn du möchtest, kannst du auch direkt mit dem Support-Team sprechen (Tippe einfach!).",
            view=SupportConfirmView(support_role)
        )

        await ticket_channel.send(view=CloseTicketView())

        await interaction.response.send_message(f"✅ Ticket erstellt: {ticket_channel.mention}", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.name.startswith("ticket-"):
        content = message.content.lower()

        keywords_allgemein = ["trading starten", "regeln", "lernbereich", "tutorial"]
        keywords_indikatoren = ["indikator", "indikatoren", "funktion", "erklärung", "was können die indikator"]
        keywords_pakete = ["paket", "preise", "upgrade"]
        keywords_whop = ["whop", "zahlung", "abo", "kündigen"]
        keywords_technik = ["channel sehen", "rolle", "discord verbinden", "zugriff"]

        recognized = False

        if any(word in content for word in keywords_allgemein):
            await message.channel.send(
                "💡 Allgemeine Infos findest du im #lernbereich und den Regeln.",
                delete_after=30)
            recognized = True
        elif any(word in content for word in keywords_indikatoren):
            await message.channel.send(
                "**Unsere Indikatoren:**\n"
                "• HELD – Starke Trend-Erkennung\n"
                "• ESXY – Volatilitäts- und Momentum-Analyse\n"
                "• COMO – Marktanalyse und Signale\n"
                "• GAPA – Breakouts & Kurslücken\n"
                "• DESC – Detailanalyse von Kursbewegungen\n"
                "• BAS – Bullnet Strategie, ca. 80% Trefferquote\n"
                "• GABO – Kombination verschiedener Signale",
                delete_after=60)
            recognized = True
        elif any(word in content for word in keywords_pakete):
            await message.channel.send(
                "**Pakete & Preise:**\n"
                "• Classic: kostenlos\n"
                "• Pro: ab 89 Euro, inkl. 5 Indikatoren, Schulungsbereich, News, Live-Calls\n"
                "• Elite: ab 299 Euro, alle Indikatoren, Bullnet Strategie mit BAS Indikator, voller Discord-Zugang\n"
                "Link: https://whop.com/bullnet-pro-ad/?a=bullnetinfo",
                delete_after=60)
            recognized = True
        elif any(word in content for word in keywords_whop):
            await message.channel.send(
                "💳 Zahlungen und Abo-Infos sind auf Whop verfügbar. Hilfe gern hier im Support!",
                delete_after=30)
            recognized = True
        elif any(word in content for word in keywords_technik):
            await message.channel.send(
                "🔧 Für Zugriffsprobleme und Discord-Verknüpfung hilft unser Support-Team.",
                delete_after=30)
            recognized = True

        if not recognized:
            support_role = None
            guild = message.guild
            if SUPPORT_ROLE_NAME.isdigit():
                support_role = guild.get_role(int(SUPPORT_ROLE_NAME))
            else:
                support_role = discord.utils.get(guild.roles, name=SUPPORT_ROLE_NAME)

            if support_role:
                await message.channel.send("Ich konnte dir nicht weiterhelfen. Möchtest du mit dem Support-Team sprechen?", view=SupportConfirmView(support_role), ephemeral=True)
            else:
                await message.channel.send("Support-Rolle nicht gefunden, bitte wende dich direkt an einen Moderator.", ephemeral=True)

    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"✅ Bot ist online als: {bot.user.name}")
    channel = bot.get_channel(TICKET_CHANNEL_ID)
    if channel:
        await channel.send("🎟️ Brauchst du Hilfe? Klicke hier, um ein Ticket zu eröffnen:", view=TicketButton())

bot.run(TOKEN)
