import socket
import requests

# Define your Twitch bot's credentials
#bot_username = 'lo_fai'
#oauth_token = 'fjxjdg3984lhmgdsptk1ii5my5xf22'
#channel = 'lo_fai'  # E.g., '#twitch_channel_name'

# lo_fai data and things and stuff
#client_id = 'ihf8dgt1iq4vnv9pjujt823pp60vn8'
#channel_id = '957095995'

def twitch_connect(bot_nick, channel, oauth_token):
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

def send_message(irc, channel, message):
    """Send a message to the Twitch channel."""
    irc.send(f"PRIVMSG #{channel} :{message}\r\n".encode('utf-8'))

def main():
    bot_nick = "lo_fai"
    channel = "lo_fai"
    oauth_token = "oauth:fjxjdg3984lhmgdsptk1ii5my5xf22"
    
    irc = twitch_connect(bot_nick, channel, oauth_token)

    # Simple loop to keep the bot running and print any incoming messages
    while True:
        response = irc.recv(2048).decode('utf-8')

        # Responding to PING messages from the server to stay connected
        if response.startswith('PING'):
            irc.send("PONG :tmi.twitch.tv\r\n".encode('utf-8'))
        
        # Check for messages in the format of PRIVMSG
        elif "PRIVMSG" in response:
            user = response.split('!', 1)[0][1:]
            message = response.split('PRIVMSG', 1)[1].split(':', 1)[1].strip()

            # If message starts with !suggest
            if message.startswith('!suggest'):
                # Split the message by spaces
                parts = message.split()
                # If there are more parts after !suggest, we consider them the suggestion
                if len(parts) > 1:
                    suggestion = ' '.join(parts[1:])
                    suggestions.append(suggestion)
                    send_message(irc, channel, f"Thank you {user}! Your suggestion has been added.")
        else:
            print(response)

if __name__ == "__main__":
    main()

