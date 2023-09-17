import socket
import time
import asyncio
import random
import ssl
from test import set_next_prompt

# Define your Twitch bot's credentials
# bot_username = 'lo_fai'
# channel = 'lo_fai'  # E.g., '#twitch_channel_name'

# lo_fai data and things and stuff
client_id = 'ihf8dgt1iq4vnv9pjujt823pp60vn8'
channel_id = '957095995'

def twitch_connect(bot_nick, channel, oauth_token):
    server = 'irc.chat.twitch.tv'
    port = 6697

    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    irc = ssl.wrap_socket(irc)  # Wrap the socket for SSL
    irc.connect((server, port))

    irc.send(f"PASS {oauth_token}\r\n".encode('utf-8'))
    irc.send(f"NICK {bot_nick}\r\n".encode('utf-8'))
    irc.send(f"JOIN #{channel}\r\n".encode('utf-8'))
    response = irc.recv(2048).decode('utf-8')
    print(response)

    return irc

suggestions = []  # List to store the suggestions

async def send_message(irc, channel, message):
    """Send a message to the Twitch channel."""
    irc.send(f"PRIVMSG #{channel} :{message}\r\n".encode('utf-8'))

async def main():
    bot_nick = "lo_fai"
    channel = "lo_fai"
    oauth_token = "oauth:iu06wjmcdcb7b8x9u18logfgdjfmh2"

    irc = twitch_connect(bot_nick, channel, oauth_token)
    
    while True:
        try:
            response = await asyncio.to_thread(irc.recv, 2048)
            response = response.decode('utf-8')

            if response.startswith('PING'):
                irc.send("PONG :tmi.twitch.tv\r\n".encode('utf-8'))
                continue
            else:
                print(response)

            await asyncio.gather(
                asyncio.sleep(30),
                look_for_suggestions(response, irc, channel)
            )

            next_prompt = await return_popular_response()
            print("The next prompt is: " + next_prompt)
            await set_next_prompt(next_prompt)

        except ConnectionResetError:
            print("Connection was reset. Trying to reconnect...")
            irc = twitch_connect(bot_nick, channel, oauth_token)


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