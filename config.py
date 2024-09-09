import json
import requests
import time
from urllib.parse import urlparse, parse_qs

# Configuration file path
config_file_path = 'config.json'

def prompt_for_input(prompt):
    return input(prompt).strip()

def create_config_file(client_id, client_secret, redirect_uri, tmdb_api_key, trakt_username):
    config = {
        'trakt_username': trakt_username,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'tmdb_api_key': tmdb_api_key
    }
    
    with open(config_file_path, 'w') as config_file:
        json.dump(config, config_file, indent=4)
    
    print(f"Configuration file '{config_file_path}' has been created successfully.")

def get_authorization_code(client_id, redirect_uri):
    auth_url = (
        f"https://trakt.tv/oauth/authorize?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
    )
    print(f"Please go to this URL and authorize the app: {auth_url}")
    
    full_redirect_url = input("Enter the full redirected URL: ")
    
    parsed_url = urlparse(full_redirect_url)
    authorization_code = parse_qs(parsed_url.query).get('code', [None])[0]
    
    if not authorization_code:
        raise ValueError("Authorization code not found in the URL")
    
    return authorization_code

def exchange_code_for_token(client_id, client_secret, redirect_uri, code):
    token_url = 'https://trakt.tv/oauth/token'
    data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    response = requests.post(token_url, data=data)
    token_data = response.json()
    
    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')
    
    return access_token, refresh_token

def save_tokens(access_token, refresh_token):
    with open(config_file_path, 'r') as config_file:
        config = json.load(config_file)
    
    config['access_token'] = access_token
    config['refresh_token'] = refresh_token
    
    with open(config_file_path, 'w') as config_file:
        json.dump(config, config_file, indent=4)
    
    print("Config file updated with new access token and refresh token.")

def refresh_access_token(client_id, client_secret, redirect_uri, refresh_token):
    token_url = 'https://trakt.tv/oauth/token'
    data = {
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'refresh_token'
    }
    response = requests.post(token_url, data=data)
    token_data = response.json()
    
    new_access_token = token_data.get('access_token')
    new_refresh_token = token_data.get('refresh_token')

    return new_access_token, new_refresh_token

def main():
    print("Welcome to the configuration setup script.")

    trakt_username = prompt_for_input("Enter your Trakt username: ")
    client_id = prompt_for_input("Enter your Trakt API client ID: ")
    client_secret = prompt_for_input("Enter your Trakt API client secret: ")
    redirect_uri = prompt_for_input("Enter your redirect URI: ")
    tmdb_api_key = prompt_for_input("Enter your TMDb API key: ")

    create_config_file(client_id, client_secret, redirect_uri, tmdb_api_key, trakt_username)

    authorization_code = get_authorization_code(client_id, redirect_uri)

    access_token, refresh_token = exchange_code_for_token(client_id, client_secret, redirect_uri, authorization_code)

    save_tokens(access_token, refresh_token)

    print("Waiting for 5 seconds before refreshing token...")
    time.sleep(5)

    new_access_token, new_refresh_token = refresh_access_token(client_id, client_secret, redirect_uri, refresh_token)
    save_tokens(new_access_token, new_refresh_token)

if __name__ == '__main__':
    main()
