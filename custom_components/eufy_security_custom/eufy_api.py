import aiohttp
import logging
import json
import uuid
import asyncio

_LOGGER = logging.getLogger(__name__)

class EufyWS:
    def __init__(self, session: aiohttp.ClientSession, ws_url: str):
        self.session = session
        self.ws_url = ws_url
        self.ws = None
        self.response_queue = {}
        self.incoming_messages = asyncio.Queue()

    async def connect_and_login(self, username, password):
        """
        Connects to the WebSocket and attempts to trigger the login via the Add-on.
        Since the add-on manages the credentials, strictly speaking we might just need to 
        listen to the status or send a 'start_listening' command to catch 2FA requests.
        """
        try:
            _LOGGER.info(f"Connecting to Eufy Station WS at {self.ws_url}")
            self.ws = await self.session.ws_connect(self.ws_url)
            
            # Start listening loop background task? 
            # For Config Flow, we'll poll read_json with timeout
            
            # Send 'start_listening' to get events
            await self.send_command("start_listening")
            
            # Give it a moment to send us current state (like captcha_request)
            return await self.wait_for_login_state()

        except Exception as e:
            _LOGGER.exception(f"WS Connection Error: {e}")
            return {"status": "error", "msg": str(e)}

    async def send_command(self, command, **kwargs):
        msg_id = str(uuid.uuid4())
        payload = {
            "messageId": msg_id,
            "command": command,
            "arguments": list(kwargs.values()) if kwargs else [] 
        }
        # Special case for driver/set_verify_code which might need specific args map
        if command == "driver.set_verify_code":
             payload["arguments"] = [kwargs.get("code")]
        if command == "driver.set_captcha":
             payload["arguments"] = [kwargs.get("captcha_id"), kwargs.get("captcha_input")]

        _LOGGER.debug(f"Sending WS: {payload}")
        await self.ws.send_json(payload)
        return msg_id

    async def wait_for_login_state(self):
        """
        Reads messages for a few seconds to see if we get a Captcha or 2FA request.
        """
        end_time = asyncio.get_event_loop().time() + 5.0 # Wait 5 seconds for status
        
        while asyncio.get_event_loop().time() < end_time:
            try:
                msg = await self.ws.receive_json(timeout=1.0)
                _LOGGER.debug(f"WS Recv: {msg}")
                
                msg_type = msg.get("type")
                
                # Check for Event: captcha request
                if msg_type == "event" and msg.get("event") == "captcha request":
                    data = msg.get("data", {}) # {captchaId, captcha}
                    return {
                        "status": "captcha_required",
                        "captcha_id": data.get("captchaId"),
                        "captcha_img": data.get("captcha")
                    }
                
                # Check for Event: verify code
                if msg_type == "event" and msg.get("event") == "verify code":
                    return {"status": "2fa_required"}
                
                # Check for Result: driver.connect result? 
                # Usually we don't send driver.connect manually if the addon handles it.

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                _LOGGER.error(f"WS Read Error: {e}")
                break
        
        # If we didn't see an error event, assume connected or strictly waiting. 
        # For the purpose of this flow, we might return "success" to create the entry, 
        # then let the user handle 2FA via a persistent notification or re-configure flow later.
        # But allow invalid_auth fallback to keep user in loop.
        return {"status": "success", "token": "ws_connected"}

    async def set_captcha(self, captcha_id, captcha_input):
        id = await self.send_command("driver.set_captcha", captcha_id=captcha_id, captcha_input=captcha_input)
        return True

    async def set_verify_code(self, code):
        id = await self.send_command("driver.set_verify_code", code=code)
        return True
    
    async def close(self):
        if self.ws:
            await self.ws.close()

