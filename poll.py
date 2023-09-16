import requests

# Define your client ID and OAuth token
client_id = 'ihf8dgt1iq4vnv9pjujt823pp60vn8'
oauth_token = '6xzio3ftg3x7zdh82dhjyybhym6ifm'

def create_poll(channel_id):
   url = f'https://api.twitch.tv/helix/polls'
   headers = {
      'Client-ID': client_id,
      'Authorization': f'Bearer {oauth_token}',
   }
   data = {
      'broadcaster_id': channel_id,
      'title': 'What should the next genre of music be?',
      'choices': ['Choice 1', 'Choice 2', 'Choice 3'],
      'duration': 30,
   }
   response = requests.post(url, headers=headers, json=data)
   return response.json()

def get_poll(channel_id):
   url = f'https://api.twitch.tv/helix/polls?broadcaster_id={channel_id}'
   headers = {
      'Client-ID': client_id,
      'Authorization': f'Bearer {oauth_token}',
   }
   response = requests.get(url, headers=headers)
   return response.json()

def tally_results(channel_id):
   poll_data = get_poll(channel_id)
   print(poll_data)

# Replace 'channel_id' with the actual channel ID you want to work with
channel_id = 'your_channel_id'

# Create and tally the poll results
create_poll(channel_id)
tally_results(channel_id)
