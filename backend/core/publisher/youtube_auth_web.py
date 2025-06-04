import os
import json
import logging
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class YouTubeAuthWeb:
    def __init__(self):
        self.credentials_file = 'config/youtube_credentials.json'
        self.token_file = 'config/youtube_token.json'
        self.scopes = ['https://www.googleapis.com/auth/youtube.upload']
        self.redirect_uri = 'http://localhost:5000/api/youtube/callback'
        logging.error(f"YouTubeAuthWeb init: {self.credentials_file}")
    
    def get_auth_url(self):
        if not os.path.exists(self.credentials_file):
            logging.error(f"Credentials file missing: {self.credentials_file}")
            raise FileNotFoundError(f"YouTube credentials file missing")
        
        flow = Flow.from_client_secrets_file(self.credentials_file, self.scopes)
        flow.redirect_uri = self.redirect_uri
        
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        with open('config/oauth_state.json', 'w') as f:
            json.dump({'state': state}, f)
        
        logging.error(f"Auth URL generated: {auth_url}")
        return auth_url
    
    def handle_callback(self, code, state):
        with open('config/oauth_state.json', 'r') as f:
            stored_state = json.load(f)['state']
        
        if state != stored_state:
            logging.error("OAuth state mismatch")
            raise ValueError("Invalid state parameter")
        
        flow = Flow.from_client_secrets_file(self.credentials_file, self.scopes)
        flow.redirect_uri = self.redirect_uri
        flow.fetch_token(code=code)
        
        with open(self.token_file, 'w') as token:
            token.write(flow.credentials.to_json())
        
        logging.error("YouTube OAuth completed")
        return flow.credentials
    
    def get_authenticated_service(self):
        credentials = None
        
        if os.path.exists(self.token_file):
            credentials = Credentials.from_authorized_user_file(self.token_file, self.scopes)
        
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                with open(self.token_file, 'w') as token:
                    token.write(credentials.to_json())
            else:
                logging.error("No valid credentials found")
                return None
        
        service = build('youtube', 'v3', credentials=credentials)
        logging.error("YouTube service authenticated")
        return service
    
    def is_authenticated(self):
        if not os.path.exists(self.token_file):
            return False
        
        try:
            credentials = Credentials.from_authorized_user_file(self.token_file, self.scopes)
            return credentials and credentials.valid
        except:
            return False
