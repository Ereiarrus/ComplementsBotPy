from src.complements_bot import ComplementsBot
import logging.config

logging_config = {
    'version': 1,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(message)s',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/complements-bot-py/app.log',
            'maxBytes': 50e6,
            'backupCount': 3,
            'formatter': 'detailed',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
}

logging.config.dictConfig(logging_config)

if __name__ == "__main__":
    bot: ComplementsBot = ComplementsBot()
    bot.run()
