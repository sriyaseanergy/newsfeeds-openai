import json
import logging
import os
import time
from datetime import datetime, timedelta

import jwt
import msal
import requests

# from app.core.config import settings
# from app.utils.app_logger import APP_LOG
# from app.utils.custom_exceptions import APIHandlingError, 
from app.core.settings import get_settings
# from app.notifications.email import TokenGenerationError


class PersonalMailService:
    """Handles authentication, retrieval, and management of emails via Microsoft Graph API."""

    def __init__(self):
        settings = get_settings()
        self.tenant_id = settings.TENANT_ID
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = ["Mail.ReadWrite"]
        self.endpoint = "https://graph.microsoft.com/v1.0"
        self.token_cache_file = "token_cache.json"
        self.token_info_file = "token_info.json"
        self.client_id = settings.CLIENT_ID

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler("mail_reader.log"), logging.StreamHandler()],
        )
        self.logger = logging.getLogger("PersonalMailService")

        # Initialize token cache and app
        self.cache = msal.SerializableTokenCache()
        self._load_token_cache()

        self.app = msal.PublicClientApplication(
            client_id=self.client_id, authority=self.authority, token_cache=self.cache
        )

    def _load_token_cache(self):
        """Load the token cache from file."""
        try:
            if os.path.exists(self.token_cache_file):
                with open(self.token_cache_file, "r") as file:
                    self.cache.deserialize(file.read())
        except Exception as e:
            self.logger.error(f"Error loading token cache: {e}")

    def _save_token_cache(self):
        """Save the token cache to file."""
        try:
            if self.cache.has_state_changed:
                with open(self.token_cache_file, "w") as file:
                    file.write(self.cache.serialize())

                # Save token info with timestamp
                token_info = {
                    "last_refresh": datetime.now().isoformat(),
                    "next_refresh": (datetime.now() + timedelta(days=85)).isoformat(),
                }
                with open(self.token_info_file, "w") as file:
                    json.dump(token_info, file)
        except Exception as e:
            self.logger.error(f"Error saving token cache: {e}")

    def _should_refresh_token(self):
        """Check if we should proactively refresh the token."""
        try:
            if os.path.exists(self.token_info_file):
                with open(self.token_info_file, "r") as file:
                    token_info = json.load(file)
                    next_refresh = datetime.fromisoformat(token_info["next_refresh"])
                    return datetime.now() >= next_refresh
        except Exception:
            self.logger.warning(
                "Token info file is missing or invalid, defaulting to refresh."
            )
        return True

    def get_token(self):
        """Get access token using cached refresh token."""
        try:
            accounts = self.app.get_accounts()
            refresh_needed = self._should_refresh_token()

            if accounts and not refresh_needed:
                result = self.app.acquire_token_silent(
                    scopes=self.scope, account=accounts[0]
                )
                if result and "access_token" in result:
                    self._save_token_cache()
                    return result["access_token"]

            # Fallback to interactive login
            self.logger.info(
                "Silent token acquisition failed or refresh needed; performing interactive login."
            )
            result = self.app.acquire_token_interactive(scopes=self.scope)

            if not result or "access_token" not in result:
                self.logger.error("Failed to acquire token.")
                raise TokenGenerationError(
                    f"Token not generated with interactive login - {result}"
                )

            self._save_token_cache()
            return result["access_token"]
        except Exception as e:
            self.logger.error(f"Error getting token: {e}")
            raise TokenGenerationError(e)

    def is_token_expired(self, token):
        """Check if the token is expired or close to expiration."""
        try:
            # Decode the token without verifying the signature
            decoded_token = jwt.decode(token, options={"verify_signature": False})

            # Extract the expiration time (exp) from the token
            exp = decoded_token.get("exp")
            if not exp:
                self.logger.error("Token does not contain an 'exp' claim.")

            expiration_time = datetime.fromtimestamp(exp)
            buffer_seconds = 300
            return datetime.now() > expiration_time - timedelta(seconds=buffer_seconds)

        except jwt.DecodeError:
            self.logger.error("Failed to decode the token.")
            return True
        except Exception as e:
            self.logger.error(f"Error decoding token: {e}")
            return True  # Assume token is expired if verification fails

    def _make_request_with_retry(
        self, url, headers, params=None, json_data=None, method="GET", retries=3
    ):
        """Make a request with retries."""
        for attempt in range(retries):
            try:
                if method == "GET":
                    response = requests.get(url, headers=headers, params=params)
                elif method == "PATCH":
                    response = requests.patch(url, headers=headers, json=json_data)
                else:
                    raise ValueError("Unsupported HTTP method")

                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt < retries - 1:
                    self.logger.warning(
                        f"Request failed ({attempt + 1}/{retries}), retrying: {e}"
                    )
                    time.sleep(2**attempt)
                else:
                    self.logger.error(f"Request failed after {retries} attempts: {e}")
                    raise APIHandlingError(f"Max retries reached for {url}: {e}")

    def get_unread_emails(self, token):
        """Get unread emails using Microsoft Graph API."""
        try:
            # Verify token before using
            if self.is_token_expired(token):
                self.logger.info("Token verification failed, getting new token.")
                token = self.get_token()

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            url = f"{self.endpoint}/me/mailFolders/inbox/messages"
            params = {
                "$filter": "isRead eq false",
                "$select": "id,subject,sender,receivedDateTime,hasAttachments,bodyPreview,body",
                "$orderby": "receivedDateTime desc",
                "$top": 50,
            }

            response = self._make_request_with_retry(url, headers, params=params)
            return response.json().get("value", [])
        except TokenGenerationError:
            self.logger.error("Error getting token")
            APP_LOG.error(
                "get_unread_emails: token generation failed; returning no messages this cycle.",
                exc_info=True,
            )
            return []
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting unread emails: {e}")
            APP_LOG.error(
                "get_unread_emails: Graph request failed after retries.",
                exc_info=True,
            )
            raise APIHandlingError(f"{url}: {e}")
        except Exception as e:
            self.logger.error(f"Error getting unread emails: {e}")
            APP_LOG.error(
                "get_unread_emails: unexpected error; returning no messages.",
                exc_info=True,
            )
            return []

    def mark_as_read(self, token, message_id):
        """Mark an email as read."""
        try:
            # Verify token before using
            if self.is_token_expired(token):
                self.logger.info("Token expired; acquiring new token.")
                token = self.get_token()

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            url = f"{self.endpoint}/me/messages/{message_id}"
            data = {"isRead": True}

            self._make_request_with_retry(url, headers, json_data=data, method="PATCH")
            return True

        except TokenGenerationError:
            return False

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error marking email as read: {e}")
            return False
