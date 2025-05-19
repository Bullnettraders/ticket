import discord
from discord.ext import commands
from discord.ui import Button, View
import openai
import os
from dotenv import load_dotenv

load_dotenv()

# === KONFIGURATION über Umgebungsvariablen ===
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
SUPPORT_ROLE_ID = int(os.getenv('SUPPORT_ROLE_ID'))
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

openai.api_key = OPENAI_API_KEY

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="🎫 Ticket eröffnen", style=discord.ButtonStyle.green, custom_id="create_ticket"))

class CloseButton(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="❌ Ticket schließen", style=discord.ButtonStyle.red, custom_id="close_ticket"))

@bot.event
async def on_ready():
    print(f"✅ Bot ist online als {bot.user}")
    channel = discord.utils.get(bot.get_all_channels(), name="support")
    if channel:
        await channel.send("Willkommen im Support! Klicke auf den Button, um ein Ticket zu eröffnen:", view=TicketView())

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.data['custom_id'] == "create_ticket":
            guild = interaction.guild
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.get_role(SUPPORT_ROLE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            ticket_channel = await guild.create_text_channel(f"ticket-{interaction.user.name}", overwrites=overwrites)
            await ticket_channel.send(
                f"Hallo {interaction.user.mention}, willkommen im Support! Stelle hier deine Frage. 🧠",
                view=CloseButton()
            )
            await interaction.response.send_message(f"✅ Dein Ticket wurde erstellt: {ticket_channel.mention}", ephemeral=True)

        elif interaction.data['custom_id'] == "close_ticket":
            await interaction.channel.send("📌 Ticket wird geschlossen...")
            await interaction.channel.delete()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.name.startswith("ticket-"):
        await message.channel.trigger_typing()
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Du bist ein hilfreicher, deutschsprachiger Support-Bot."},
                    {"role": "user", "content": message.content}
                ]
            )
            reply = response.choices[0].message.content
            await message.channel.send(reply)
        except Exception as e:
            await message.channel.send(f"⚠️ Fehler bei der AI-Antwort: {str(e)}")

support_role_env = os.getenv('SUPPORT_ROLE_ID')
if support_role_env is None:
    raise ValueError("❌ Umgebungsvariable SUPPORT_ROLE_ID fehlt!")
SUPPORT_ROLE_ID = int(support_role_env)


bot.run(TOKEN)
