import telegram
import asyncio

async def send_telegram_message(chat_id, message):
    bot = telegram.Bot(token='8149347717:AAEJE7gewB0KjCsybxYZjubqyaKspZ9TLtM')
    await bot.send_message(chat_id=chat_id, text=message)

if __name__ == "__main__":
    # Prueba de envío de mensaje al canal
    try:
        asyncio.run(send_telegram_message(
            chat_id='@agrolucha',
            message='Prueba de integración: mensaje enviado desde telegram_utils.py'
        ))
        print("Mensaje enviado correctamente.")
    except Exception as e:
        print(f"Error al enviar el mensaje: {e}")