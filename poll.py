import socket
import time
import asyncio
import random
from test import set_next_prompt

# Define your Twitch bot's credentials
# bot_username = 'lo_fai'
# oauth_token = 'fjxjdg3984lhmgdsptk1ii5my5xf22'
# channel = 'lo_fai'  # E.g., '#twitch_channel_name'

# lo_fai data and things and stuff
client_id = 'ihf8dgt1iq4vnv9pjujt823pp60vn8'
channel_id = '957095995'

async def twitch_connect(bot_nick, channel, oauth_token):
    server = 'irc.chat.twitch.tv'
    port = 6667

    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    irc.connect((server, port))

    # Authenticate with the server
    irc.send(f"PASS {oauth_token}\r\n".encode('utf-8'))
    irc.send(f"NICK {bot_nick}\r\n".encode('utf-8'))
    irc.send(f"JOIN #{channel}\r\n".encode('utf-8'))

    return irc

suggestions = []  # List to store the suggestions

async def send_message(irc, channel, message):
    """Send a message to the Twitch channel."""
    irc.send(f"PRIVMSG #{channel} :{message}\r\n".encode('utf-8'))

async def main():
    bot_nick = "lo_fai"
    channel = "lo_fai"
    oauth_token = "oauth:fjxjdg3984lhmgdsptk1ii5my5xf22"
    
    irc = await twitch_connect(bot_nick, channel, oauth_token)

    start_time = time.time()
    end_time = start_time + 30
    
    # Simple loop to keep the bot running and print any incoming messages
    while True:
        response = irc.recv(2048).decode('utf-8')

        wait_time_task = await asyncio.to_thread(asyncio.sleep, 30)

        # Responding to PING messages from the server to stay connected
        if response.startswith('PING'):
            irc.send("PONG :tmi.twitch.tv\r\n".encode('utf-8'))
        else:
            print(response)

        # Check for messages in the format of PRIVMSG
        look_for_suggestion_task = await asyncio.to_thread(look_for_suggestions, response, irc, channel)

        # Wait and look for suggestions concurrently
        await asyncio.gather(wait_time_task, look_for_suggestion_task)

        # Grab an element randomly from the list and clear it
        next_prompt = await return_popular_response()
        print("The next prompt is: " + next_prompt)
        # And here we send this to the AI model
        set_next_prompt(next_prompt)


async def look_for_suggestions(response, irc, channel):
    global suggestions

    if ("PRIVMSG" not in response):
        return
    user = response.split('!', 1)[0][1:]
    message = response.split('PRIVMSG', 1)[1].split(':', 1)[1].strip()

    # If message starts with !suggest
    if message.startswith('!suggest'):
        # Split the message by spaces
        parts = message.split()
        # If there are more parts after !suggest, we consider them the suggestion
        if len(parts) > 1:
            suggestion = ' '.join(parts[1:])
            print(suggestion + " has been added to suggestions")
            suggestions.append(suggestion)
            await send_message(irc, channel, f"Your suggestion {suggestion} has been added.")

# Finish this
async def return_popular_response():
    global suggestions

    if not suggestions:
        return "calming lo-fi"
    chosen_suggestion = random.choice(suggestions)
    suggestions.clear()
    return chosen_suggestion


if __name__ == "__main__":
    asyncio.run(main())