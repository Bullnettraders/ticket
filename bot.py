import discord
from discord.ext import commands
from discord import Interaction, ButtonStyle
from discord.ui import Button, View
from openai import OpenAI
import tiktoken
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

GUILD_ID = int(os.getenv("GUILD_ID"))
SUPPORT_ROLE_ID = int(os.getenv("SUPPORT_ROLE_ID"))
CATEGORY_ID = int(os.getenv("CATEGORY_ID"))
SUPPORT_CHANNEL_ID = int(os.getenv("SUPPORT_CHANNEL_ID"))
ADMIN_LOG_CHANNEL_ID = int(os.getenv("ADMIN_LOG_CHANNEL_ID"))

def estimate_openai_cost(messages, model="gpt-3.5-turbo"):
    encoding = tiktoken.encoding_for_model(model)
    total_tokens = sum(len(encoding.encode(m["content"])) for m in messages)
    price_per_1k = 0.002
    return total_tokens, (total_tokens / 1000) * price_per_1k

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ticket erstellen", style=ButtonStyle.green, custom_id="create_ticket")
    async def create_ticket(self, interaction: Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        category = discord.utils.get(guild.categories, id=CATEGORY_ID)
        existing = discord.utils.get(guild.text_channels, name=f"ticket-{interaction.user.name.lower()}")

        if existing:
            await interaction.followup.send(f"Du hast bereits ein offenes Ticket: {existing.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.get_role(SUPPORT_ROLE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel = await guild.create_text_channel(f"ticket-{interaction.user.name}", category=category, overwrites=overwrites)
        await channel.send(f"Hallo {interaction.user.mention}, willkommen im Support. Bitte schildere dein Problem.")

        roles = [r.name for r in guild.roles if not r.is_default()]
        channels = [c.name for c in guild.text_channels]

        info_prompt = (
            f"Du bist Kalle, der Support-Bot für den Discord-Server '{guild.name}'. "
            f"Auf diesem Server gibt es folgende Rollen: {', '.join(roles)}. "
            f"Die verfügbaren Textkanäle sind: {', '.join(channels)}. "
            f"Beantworte ausschließlich Fragen zum Server, zu Rollen, Kanälen oder den Regeln. "
            f"Alle anderen Themen (z. B. Technik, Programmierung) lehnst du höflich ab."
        )

        messages = [
            {"role": "system", "content": info_prompt},
            {"role": "user", "content": "Der Benutzer hat soeben ein Ticket eröffnet, bitte begrüße ihn."}
        ]

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            ai_reply = response.choices[0].message.content
        except Exception as e:
            ai_reply = f"⚠️ Konnte keine Antwort von der AI erhalten. Fehler: {str(e)}"

        messages.append({"role": "assistant", "content": ai_reply})
        tokens_used, cost = estimate_openai_cost(messages)

        await channel.send(f"AI: {ai_reply}")

        log_channel = bot.get_channel(ADMIN_LOG_CHANNEL_ID)
        if log_channel:
            log_text = (
                f"📊 Kostenübersicht:\n"
                f"Benutzer: {interaction.user.mention}\n"
                f"Tokenverbrauch: {tokens_used}\n"
                f"Kosten: **{cost:.5f} USD**"
            )
            await log_channel.send(log_text)

        close_view = CloseTicketView()
        await channel.send("Wenn dein Problem gelöst wurde, kannst du das Ticket schließen:", view=close_view)
        await interaction.followup.send(f"Dein Ticket wurde erstellt: {channel.mention}", ephemeral=True)

class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="❌ Ticket schließen", style=ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: Interaction, button: Button):
        await interaction.response.send_message("Ticket wird geschlossen...", ephemeral=True)
        await interaction.channel.delete()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.channel.name.startswith("ticket-"):
        roles = [r.name for r in message.guild.roles if not r.is_default()]
        channels = [c.name for c in message.guild.text_channels]
        info_prompt = (
            f"Du bist Kalle, der Support-Bot für den Discord-Server '{message.guild.name}'. "
            f"Auf diesem Server gibt es folgende Rollen: {', '.join(roles)}. "
            f"Die verfügbaren Textkanäle sind: {', '.join(channels)}. "
            f"Beantworte ausschließlich Fragen zum Server, zu Rollen, Kanälen oder den Regeln. "
            f"Alle anderen Themen (z. B. Technik, Programmierung) lehnst du höflich ab."
        )
        messages = [
            {"role": "system", "content": info_prompt},
            {"role": "user", "content": message.content}
        ]
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            ai_reply = response.choices[0].message.content
            await message.channel.send(f"AI: {ai_reply}")
        except Exception as e:
            await message.channel.send(f"⚠️ Konnte nicht antworten: {str(e)}")

@bot.event
async def on_ready():
    print(f"Bot ist online als {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Slash Commands synchronisiert: {len(synced)}")
    except Exception as e:
        print(e)
    channel = bot.get_channel(SUPPORT_CHANNEL_ID)
    if channel:
        view = TicketView()
        await channel.send("**Brauchst du Hilfe?**\nKlicke auf den Button, um ein Support-Ticket zu erstellen.", view=view)

bot.run(os.getenv("DISCORD_TOKEN"))
