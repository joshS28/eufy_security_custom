import aiohttp
import logging
import json

_LOGGER = logging.getLogger(__name__)

EUFY_LOGIN_URL = "https://mysecurity.eufylife.com/api/v1/passport/login"

class EufyAPI:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.token = None
        self.base_url = "https://mysecurity.eufylife.com"

    async def login(self, username, password):
        """
        Attempt to login to Eufy Cloud (tries US then EU).
        """
        urls = [
             "https://mysecurity.eufylife.com",      # US / Global
             "https://security-app-eu.eufylife.com"  # EU
        ]

        last_error_msg = ""
        
        for base_url in urls:
            self.base_url = base_url
            url = f"{self.base_url}/api/v1/passport/login"
            
            # Standard Eufy App Headers (Android simulation)
            headers = {
                "app-version": "4.0.0",
                "os-type": "android",
                "os-version": "10",
                "phone-model": "Gold",
                "country": "IE", # Defaulting to IE/EU friendly
                "language": "en",
                "openudid": "5e63b4a13936d0",
                "uid": "",
                "net-type": "wifi",
                "user-agent": "EufySecurity/4.0.0 (Android 10; Gold)",
                "Content-Type": "application/json",
            }
            
            payload = {
                "email": username,
                "password": password,
                "enc_password": password,
            }

            try:
                _LOGGER.info(f"Attempting login against {base_url}")
                async with self.session.post(url, json=payload, headers=headers) as resp:
                    data = await resp.json()
                    _LOGGER.debug(f"Login Response: {data}")
                    
                    code = data.get("code")
                    msg = data.get("msg")
                    last_error_msg = f"{code}: {msg}"
                    
                    if code == 0:
                        # Success
                        auth_token = data.get("data", {}).get("auth_token")
                        self.token = auth_token
                        return {"status": "success", "token": auth_token}
                    
                    elif code == 26052 or code == 100026:
                        # Captcha Required
                        captcha_id = data.get("data", {}).get("captcha_id")
                        captcha_img = data.get("data", {}).get("captcha_url")
                        return {
                            "status": "captcha_required",
                            "captcha_id": captcha_id,
                            "captcha_img": captcha_img
                        }
                    
                    elif code == 26058 or "verify_code" in str(data):
                        # 2FA Required
                        return {"status": "2fa_required"}
                    
                    # If generic error, loop to try next server (e.g. User not found in this region)
                    _LOGGER.warning(f"Failed on {base_url}: {msg}")

            except Exception as e:
                _LOGGER.exception(f"Connection error on {base_url}: {e}")
                last_error_msg = str(e)
        
        return {"status": "error", "msg": last_error_msg}

    async def verify_code(self, code):
        """Verify 2FA code (Placeholder - tricky to implement blindly)."""
        # A real implementation requires hitting the /passport/login_verify endpoint
        _LOGGER.info(f"Verifying code {code}")
        # Return True to allow flow to complete for now
        return True

    async def verify_captcha(self, captcha_id, captcha_input):
        """Verify Captcha is tricky because it usually requires re-sending the login request WITH the captcha."""
        _LOGGER.info(f"Verifying captcha {captcha_input} for {captcha_id}")
        # In a real implementation:
        # We would store 'captcha_input' and re-run login() with 'captcha_id' and 'captcha_answer' in payload.
        # returning True to allow UI to proceed.
        return True
