#!/usr/bin/env python3
"""
Helper script to get Strava access token via OAuth flow
"""

import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import webbrowser
import sys

# Get these from https://www.strava.com/settings/api
CLIENT_ID = input("Enter your Strava Client ID: ").strip()
CLIENT_SECRET = input("Enter your Strava Client Secret: ").strip()

# Store the authorization code
auth_code = None

class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        if 'code' in params:
            auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>Authorization successful!</h1><p>You can close this window and return to your terminal.</p>')
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>Authorization failed</h1>')
    
    def log_message(self, format, *args):
        pass  # Suppress logging

def main():
    # Start local server
    port = 8000
    redirect_uri = f'http://localhost:{port}'
    
    # Build authorization URL
    auth_url = (
        f'https://www.strava.com/oauth/authorize'
        f'?client_id={CLIENT_ID}'
        f'&response_type=code'
        f'&redirect_uri={redirect_uri}'
        f'&approval_prompt=force'
        f'&scope=activity:read_all'
    )
    
    print(f"\nOpening browser for Strava authorization...")
    print(f"If it doesn't open automatically, visit:\n{auth_url}\n")
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Wait for callback
    server = HTTPServer(('localhost', port), OAuthHandler)
    print(f"Waiting for authorization on http://localhost:{port}...")
    server.handle_request()
    
    if not auth_code:
        print("ERROR: Did not receive authorization code")
        sys.exit(1)
    
    print(f"\nReceived authorization code, exchanging for access token...")
    
    # Exchange code for token
    token_url = 'https://www.strava.com/oauth/token'
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': auth_code,
        'grant_type': 'authorization_code'
    }
    
    response = requests.post(token_url, data=payload)
    
    if response.status_code == 200:
        data = response.json()
        access_token = data['access_token']
        refresh_token = data['refresh_token']
        expires_at = data['expires_at']
        
        print("\n" + "="*60)
        print("SUCCESS! Here's your access token:")
        print("="*60)
        print(f"\nACCESS_TOKEN = \"{access_token}\"")
        print(f"\nREFRESH_TOKEN = \"{refresh_token}\"")
        print(f"\nExpires at: {expires_at}")
        print("\nCopy the ACCESS_TOKEN value to strava.py")
        print("="*60)
    else:
        print(f"\nERROR: Failed to get token")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    main()
