import requests
from urllib.parse import urlencode

def authenticate_twitch(client_id, client_secret, redirect_uri, scope):
    # Step 1: Generate the authorization URL
    authorize_url = 'https://id.twitch.tv/oauth2/authorize'
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': scope,
    }
    
    authorization_url = authorize_url + '?' + urlencode(params)
    
    print(f'Open the following URL in your browser and grant access:\n{authorization_url}')
    
    # Step 2: User grants access and is redirected back with a code
    authorization_code = input('Enter the code from the redirect URL: ')
    
    # Step 3: Exchange the code for an access token
    token_url = 'https://id.twitch.tv/oauth2/token'
    token_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': authorization_code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
    }
    
    response = requests.post(token_url, data=token_data)
    
    if response.status_code == 200:
        access_token = response.json()['access_token']
        return access_token
    else:
        print(f'Error getting access token: {response.text}')
        return None

if __name__ == '__main__':
    client_id = 'r6tbyrbhqebfd12lslot06myjqb1hm'
    client_secret = '9pnpl9enexuyhm6sszws94ffonqpld'
    redirect_uri = 'http://localhost:3000'
    scope = 'chat:edit chat:read'
    
    access_token = authenticate_twitch(client_id, client_secret, redirect_uri, scope)
    
    if access_token:
        print(f'Access Token: {access_token}')
