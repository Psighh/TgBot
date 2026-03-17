import logging
from telegram.ext import Application, MessageHandler, filters
from config import TOKEN
import network 

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.ERROR
)

def main():
    app = (
        Application.builder()
        .token(TOKEN)
        .post_init(network.post_init)
        .post_shutdown(network.post_shutdown)
        .build()
    )

    app.add_error_handler(network.error_handler)

    app.add_handler(MessageHandler(
        filters.TEXT | filters.Sticker.ALL, 
        network.check_network_status
    ))

    app.run_polling()

if __name__ == "__main__":
    main()