#!/usr/bin/env python3
"""Automated OAuth 2.0 Setup for YouTube and X (Twitter).

This script automates the OAuth flow:
1. Starts a local HTTP server to handle callbacks
2. Opens your browser for authorization
3. Exchanges the code for tokens
4. Saves tokens to a local config file
5. Prints instructions for GitHub Secrets

Usage:
    python scripts/setup_oauth.py youtube
    python scripts/setup_oauth.py x
    python scripts/setup_oauth.py all
"""
import http.server
import json
import os
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser

# ---- Configuration ----
REDIRECT_PORT = 8080
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}"
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")
TOKENS_FILE = os.path.join(CONFIG_DIR, "oauth_tokens.json")

# YouTube OAuth config (you need to create this in Google Cloud Console)
YOUTUBE_SCOPES = "https://www.googleapis.com/auth/youtube.readonly"

# X OAuth config (you need to create this in X Developer Portal)
X_SCOPES = "bookmark.read tweet.read users.read"


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """Handle OAuth callback and extract authorization code."""
    
    auth_code = None
    
    def do_GET(self):
        """Handle the OAuth callback."""
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        if "code" in params:
            OAuthCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"""
                <html><body>
                <h1>Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                </body></html>
            """)
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"""
                <html><body>
                <h1>Authorization Failed</h1>
                <p>No authorization code received.</p>
                </body></html>
            """)
    
    def log_message(self, format, *args):
        """Suppress server logs."""
        pass


def start_callback_server(port):
    """Start a local HTTP server to handle OAuth callbacks."""
    server = http.server.HTTPServer(("localhost", port), OAuthCallbackHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    return server


def exchange_code_for_tokens(code, platform):
    """Exchange authorization code for access and refresh tokens."""
    
    if platform == "youtube":
        # Get client ID and secret from user
        client_id = input("Enter YouTube Client ID: ").strip()
        client_secret = input("Enter YouTube Client Secret: ").strip()
        
        data = urllib.parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        }).encode("utf-8")
        
        req = urllib.request.Request(
            "https://oauth2.googleapis.com/token",
            data=data,
            method="POST",
        )
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        
    elif platform == "x":
        # Get client ID and secret from user
        client_id = input("Enter X Client ID: ").strip()
        client_secret = input("Enter X Client Secret: ").strip()
        
        data = urllib.parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "code_verifier": "challenge",
        }).encode("utf-8")
        
        req = urllib.request.Request(
            "https://api.twitter.com/2/oauth2/token",
            data=data,
            method="POST",
        )
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    with urllib.request.urlopen(req, timeout=15) as resp:
        tokens = json.loads(resp.read().decode("utf-8"))
    
    return tokens


def get_x_user_id(access_token):
    """Get X user ID from access token."""
    req = urllib.request.Request(
        "https://api.twitter.com/2/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["data"]["id"]


def save_tokens(platform, tokens, extra_data=None):
    """Save tokens to config file."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    
    # Load existing config
    config = {}
    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, "r") as f:
            config = json.load(f)
    
    # Add new tokens
    if platform == "youtube":
        config["youtube"] = {
            "client_id": tokens.get("client_id", ""),
            "client_secret": tokens.get("client_secret", ""),
            "refresh_token": tokens.get("refresh_token", ""),
        }
    elif platform == "x":
        config["x"] = {
            "user_id": extra_data.get("user_id", ""),
            "access_token": tokens.get("access_token", ""),
        }
    
    # Save
    with open(TOKENS_FILE, "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Tokens saved to {TOKENS_FILE}")


def setup_youtube():
    """Setup YouTube OAuth 2.0."""
    print("=" * 60)
    print("YouTube OAuth 2.0 Setup")
    print("=" * 60)
    print()
    print("This script will help you set up YouTube OAuth 2.0")
    print("to access your liked videos.")
    print()
    print("Prerequisites:")
    print("1. A Google Cloud project with YouTube Data API v3 enabled")
    print("2. OAuth 2.0 credentials (Client ID and Client Secret)")
    print()
    print("If you haven't created these yet, follow the instructions in:")
    print("  API_GUIDE.md → Section 4.2 YouTube Liked Videos")
    print()
    
    input("Press Enter when ready...")
    
    # Start callback server
    print(f"\nStarting local server on port {REDIRECT_PORT}...")
    server = start_callback_server(REDIRECT_PORT)
    
    # Build authorization URL
    client_id = input("Enter YouTube Client ID: ").strip()
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"response_type=code&"
        f"scope={YOUTUBE_SCOPES}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    print(f"\nOpening browser for authorization...")
    print(f"If the browser doesn't open, manually visit:")
    print(f"  {auth_url}")
    print()
    
    webbrowser.open(auth_url)
    
    # Wait for callback
    print("Waiting for authorization...")
    while OAuthCallbackHandler.auth_code is None:
        time.sleep(0.1)
    
    code = OAuthCallbackHandler.auth_code
    server.shutdown()
    
    print(f"\nReceived authorization code!")
    print("Exchanging code for tokens...")
    
    # Exchange code for tokens
    tokens = exchange_code_for_tokens(code, "youtube")
    tokens["client_id"] = client_id
    
    # Save tokens
    save_tokens("youtube", tokens)
    
    # Print instructions
    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print()
    print("Add these secrets to your GitHub repository:")
    print("  https://github.com/Jacky-0809/ai-project-tracker/settings/secrets/actions")
    print()
    print("Secrets to add:")
    print(f"  YOUTUBE_CLIENT_ID = {client_id}")
    print(f"  YOUTUBE_CLIENT_SECRET = {tokens.get('client_secret', 'YOUR_SECRET')}")
    print(f"  YOUTUBE_REFRESH_TOKEN = {tokens.get('refresh_token', 'YOUR_TOKEN')}")
    print()
    print("Test locally with:")
    print("  python scripts/scrapers/youtube_liked_scraper.py")
    print()


def setup_x():
    """Setup X (Twitter) OAuth 2.0."""
    print("=" * 60)
    print("X (Twitter) OAuth 2.0 Setup")
    print("=" * 60)
    print()
    print("This script will help you set up X OAuth 2.0")
    print("to access your bookmarks.")
    print()
    print("Prerequisites:")
    print("1. An X Developer account")
    print("2. An App with OAuth 2.0 enabled")
    print("3. User authentication settings configured")
    print()
    print("If you haven't created these yet, follow the instructions in:")
    print("  API_GUIDE.md → Section 4.1 X Bookmarks")
    print()
    
    input("Press Enter when ready...")
    
    # Start callback server
    print(f"\nStarting local server on port {REDIRECT_PORT}...")
    server = start_callback_server(REDIRECT_PORT)
    
    # Build authorization URL
    client_id = input("Enter X Client ID: ").strip()
    auth_url = (
        f"https://twitter.com/i/oauth2/authorize?"
        f"client_id={client_id}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"response_type=code&"
        f"scope={X_SCOPES}&"
        f"state=xyz&"
        f"code_challenge=challenge&"
        f"code_challenge_method=plain"
    )
    
    print(f"\nOpening browser for authorization...")
    print(f"If the browser doesn't open, manually visit:")
    print(f"  {auth_url}")
    print()
    
    webbrowser.open(auth_url)
    
    # Wait for callback
    print("Waiting for authorization...")
    while OAuthCallbackHandler.auth_code is None:
        time.sleep(0.1)
    
    code = OAuthCallbackHandler.auth_code
    server.shutdown()
    
    print(f"\nReceived authorization code!")
    print("Exchanging code for tokens...")
    
    # Exchange code for tokens
    tokens = exchange_code_for_tokens(code, "x")
    
    # Get user ID
    print("Getting user ID...")
    user_id = get_x_user_id(tokens["access_token"])
    
    # Save tokens
    save_tokens("x", tokens, {"user_id": user_id})
    
    # Print instructions
    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print()
    print("Add these secrets to your GitHub repository:")
    print("  https://github.com/Jacky-0809/ai-project-tracker/settings/secrets/actions")
    print()
    print("Secrets to add:")
    print(f"  X_USER_ID = {user_id}")
    print(f"  X_ACCESS_TOKEN = {tokens.get('access_token', 'YOUR_TOKEN')}")
    print()
    print("Test locally with:")
    print("  python scripts/scrapers/x_bookmarks_scraper.py")
    print()


def setup_all():
    """Setup both YouTube and X OAuth."""
    print("=" * 60)
    print("Complete OAuth 2.0 Setup")
    print("=" * 60)
    print()
    print("This script will set up both YouTube and X OAuth 2.0")
    print("to access your liked videos and bookmarks.")
    print()
    
    # YouTube setup
    print("\n--- YouTube Setup ---\n")
    setup_youtube()
    
    # X setup
    print("\n--- X Setup ---\n")
    setup_x()
    
    # Final instructions
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print("Your tokens have been saved to:")
    print(f"  {TOKENS_FILE}")
    print()
    print("Next steps:")
    print("1. Add all secrets to GitHub (see instructions above)")
    print("2. Test locally:")
    print("   python scripts/run.py --date 2026-09-04")
    print("3. Commit and push to trigger CI:")
    print("   git add . && git commit -m 'feat: add OAuth tokens' && git push")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/setup_oauth.py [youtube|x|all]")
        sys.exit(1)
    
    platform = sys.argv[1].lower()
    
    if platform == "youtube":
        setup_youtube()
    elif platform == "x":
        setup_x()
    elif platform == "all":
        setup_all()
    else:
        print(f"Unknown platform: {platform}")
        print("Usage: python scripts/setup_oauth.py [youtube|x|all]")
        sys.exit(1)
