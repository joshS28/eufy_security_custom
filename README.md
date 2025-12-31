# Eufy Security Custom Integration

This is a custom integration for Home Assistant to connect to Eufy Security devices.
It connects directly to the Eufy cloud API (handling 2FA and Captcha) instead of relying on an external Docker bridge.

## Features
- **Direct Authentication**: Handles Eufy's 2FA and Captcha challenges natively in the Home Assistant Config Flow.
- **HACS Compatible**: Ready to be added as a custom repository in HACS.

## Installation

1. Copy the `custom_components/eufy_security_custom` folder to your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Go to **Settings > Devices & Services > Add Integration**.
4. Search for "Eufy Security Custom".
5. Enter your email and password.
6. If prompted, enter the 2FA code or Captcha.

## Development

This module structure is set up to handle the multi-step authentication required by Eufy.
The core logic resides in `eufy_api.py`. Currently, this is a placeholder and needs to be connected to a functional Eufy Python library or implemented with specific API endpoints.

## Publish to HACS
1. Push this code to a GitHub repository.
2. In HACS, go to **Integrations > Top Right Menu > Custom Repositories**.
3. Add your GitHub URL and select "Integration".
