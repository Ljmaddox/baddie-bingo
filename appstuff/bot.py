import discord
import os
from flask import Flask, request, jsonify
from threading import Thread
from discord.ext import tasks
from queue import Queue

# Define intents and create an instance of a client with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
app = Flask(__name__)

# Discord token from environment variables
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable not set.")

# Queue for storing bingo messages
queue = Queue()

@app.route('/bingo', methods=['POST'])
def bingo():
    data = request.json
    player_name = data.get('name')
    message = data.get('message')

    if not player_name or not message:
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400

    queue.put((player_name, message))
    return jsonify({'status': 'received'}), 200

@tasks.loop(seconds=1)
async def process_bingo_queue():
    while not queue.empty():
        player_name, message = queue.get()
        await send_message_to_discord(player_name, message)

async def send_message_to_discord(player_name, message):
    channel = find_channel_with_permissions()
    if channel:
        player_id = await get_member_id(channel.guild, player_name)
        if player_id:
            mention = f'<@{player_id}>'
            await channel.send(f'{mention} {message}')
        else:
            print(f"Player '{player_name}' not found in the server.")
    else:
        print("No suitable channel found for sending the message.")

def find_channel_with_permissions():
    for guild in client.guilds:
        for channel in guild.text_channels:
            permissions = channel.permissions_for(guild.me)
            if permissions.send_messages:
                return channel
    return None

async def get_member_id(guild, player_name):
    for member in guild.members:
        if player_name and (player_name.lower() == member.name.lower() or player_name.lower() == member.display_name.lower()):
            return member.id
    return None

def run_flask():
    app.run(port=5001)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    process_bingo_queue.start()

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    client.run(DISCORD_TOKEN)
