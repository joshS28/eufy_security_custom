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
        Attempt to login mimicking the Eufy Web Portal (Chrome).
        This avoids the complex signature requirements of the mobile app API.
        """
        # The Web Portal API endpoint
        url = "https://mysecurity.eufylife.com/api/v1/passport/login"
        self.base_url = "https://mysecurity.eufylife.com"

        # Headers mimicking a standard Desktop Browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://mysecurity.eufylife.com",
            "Referer": "https://mysecurity.eufylife.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            # Sometimes required for API consistency
            "timezone": "Europe/Dublin", 
            "country": "IE"
        }
        
        payload = {
            "email": username,
            "password": password,
        }

        try:
            _LOGGER.warning(f"Attempting Web Portal login: {url}")
            async with self.session.post(url, json=payload, headers=headers) as resp:
                text_response = await resp.text()
                
                # Debug logging - Force Warning for visibility during debug
                _LOGGER.warning(f"Status: {resp.status}")
                if len(text_response) > 200:
                     _LOGGER.warning(f"Response: {text_response[:200]}...")
                else:
                     _LOGGER.warning(f"Response: {text_response}")

                try:
                    data = json.loads(text_response)
                except json.JSONDecodeError:
                     # If we get HTML (405/403), it's a hard block.
                     _LOGGER.warning(f"HARD FAILURE: Non-JSON response: {resp.status}")
                     return {"status": "error", "msg": f"Non-JSON response: {resp.status}"}

                code = data.get("code")
                msg = data.get("msg")
                
                if code == 0:
                    # Success
                    auth_token = data.get("data", {}).get("auth_token")
                    self.token = auth_token
                    _LOGGER.warning("Login Successful!")
                    return {"status": "success", "token": auth_token}
                
                elif code == 26052 or code == 100026:
                    _LOGGER.warning("Captcha Required")
                    return {
                        "status": "captcha_required",
                        "captcha_id": data.get("data", {}).get("captcha_id"),
                        "captcha_img": data.get("data", {}).get("captcha_url")
                    }
                
                elif code == 26058 or "verify_code" in str(data):
                    _LOGGER.warning("2FA Required")
                    return {"status": "2fa_required"}
                
                else:
                    _LOGGER.warning(f"Eufy API Error: {code} - {msg}")
                    return {"status": "error", "msg": msg}

        except Exception as e:
            _LOGGER.warning(f"Connection error: {e}")
            return {"status": "error", "msg": str(e)}

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
