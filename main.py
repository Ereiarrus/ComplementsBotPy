from src.complements_bot import ComplementsBot, catch_exceptions_decorator


@catch_exceptions_decorator
def starting():
    bot: ComplementsBot = ComplementsBot()
    bot.run()


if __name__ == "__main__":
    starting()
