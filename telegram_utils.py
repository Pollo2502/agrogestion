import requests

BOT_TOKEN = '8508713559:AAGuigERCjG7ppMbmheV-RXYcdTmD-NWykE'
CHAT_ID = '-5039857643'

def send_telegram_message(message):
    """
    Sends a message to the specified Telegram chat using the bot token.
    """
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")