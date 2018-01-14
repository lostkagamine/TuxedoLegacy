import argparse

class DiscordArgparseError(Exception):
    pass


class DiscordArgparseMessage(DiscordArgparseError):
    pass


class DiscordFriendlyArgparse(argparse.ArgumentParser):
    def _print_message(self, message, file=None):
        raise DiscordArgparseMessage(f'```\n{message}\n```')

    def error(self, message):
        raise DiscordArgparseError(f'```\n{self.format_usage()}\nerror: {message}\n```')