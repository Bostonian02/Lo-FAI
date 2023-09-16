import requests

# Replace with your Client ID and the channel username
client_id = 'ihf8dgt1iq4vnv9pjujt823pp60vn8'
username = 'ludwig'

# Define the endpoint URL
url = f'https://api.twitch.tv/helix/users?login={username}'

# Set up the headers with your Client ID and an OAuth token (not needed for this request)
headers = {
    'Client-ID': client_id,
    'Authorization': 'Bearer 1zjhpe6cmfmvbix2q1vg1bcx3uqoho',  
}

# Make the API request
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    data = response.json()
    if 'data' in data and len(data['data']) > 0:
        channel_id = data['data'][0]['id']
        print(f'The channel ID for {username} is: {channel_id}')
    else:
        print(f'Channel {username} not found.')
else:
    print(f'Error: {response.status_code} - {response.text}')