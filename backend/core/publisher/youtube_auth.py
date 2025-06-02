import os
import json
import logging
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class YouTubeAuth:
    def __init__(self):
        self.credentials_file = 'config/youtube_credentials.json'
        self.token_file = 'config/youtube_token.json'
        self.scopes = ['https://www.googleapis.com/auth/youtube.upload']
        logging.info("YouTubeAuth initialized")
    
    def get_authenticated_service(self):
        credentials = self._get_credentials()
        service = build('youtube', 'v3', credentials=credentials)
        logging.info("YouTube service authenticated")
        return service
    
    def _get_credentials(self):
        credentials = None
        
        if os.path.exists(self.token_file):
            credentials = Credentials.from_authorized_user_file(self.token_file, self.scopes)
        
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                logging.info("Credentials refreshed")
            else:
                credentials = self._authorize_new_credentials()
            
            with open(self.token_file, 'w') as token:
                token.write(credentials.to_json())
        
        return credentials
    
    def _authorize_new_credentials(self):
        if not os.path.exists(self.credentials_file):
            logging.error(f"Credentials file not found: {self.credentials_file}")
            raise FileNotFoundError(
                f"YouTube credentials file not found: {self.credentials_file}\n"
                "Please download from Google Cloud Console and place in config folder"
            )
        
        flow = Flow.from_client_secrets_file(self.credentials_file, self.scopes)
        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        
        auth_url, _ = flow.authorization_url(prompt='consent')
        logging.info(f"Authorization URL: {auth_url}")
        
        print(f"Please visit this URL to authorize: {auth_url}")
        auth_code = input("Enter authorization code: ")
        
        flow.fetch_token(code=auth_code)
        logging.info("New credentials authorized")
        return flow.credentials
