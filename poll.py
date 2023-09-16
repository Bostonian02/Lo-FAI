import socket

# Define your Twitch bot's credentials
bot_username = 'lo_fai'
oauth_token = 'kpa1bx0ismg7mq2emkfpuyxl9bo34p'
channel = 'lo_fai'  # E.g., '#twitch_channel_name'

# lo_fai data and things and stuff
client_id = 'ihf8dgt1iq4vnv9pjujt823pp60vn8'
channel_id = '957095995'

# Connect to the Twitch IRC server
server = 'irc.twitch.tv'
port = 3000

irc = socket.socket()
irc.connect((server, port))

# Authenticate with Twitch IRC using your OAuth token and bot username
irc.send(f'PASS {oauth_token}\n'.encode('utf-8'))
irc.send(f'NICK {bot_username}\n'.encode('utf-8'))

# Join the desired Twitch channel
irc.send(f'JOIN {channel}\n'.encode('utf-8'))

# Start listening for messages
while True:
    message = irc.recv(2048).decode('utf-8')
    if message.startswith('PING'):
        irc.send('PONG\n'.encode('utf-8'))  # Respond to Twitch's PING requests
    elif 'PRIVMSG' in message:
        user = message.split('!', 1)[0][1:]
        message_content = message.split('PRIVMSG', 1)[1].split(':', 1)[1]
        print(f'{user}: {message_content}')


