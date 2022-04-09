import typing
from PIL import ImageFont
from .helpers import get_nodes


__all__ = [
    'BaseRequester',
    'BasePilmoji'
]


class BasePilmoji:
    """
    The base emoji render that all renderes must inherit from.
    """
    @staticmethod
    def getsize(text: str, font=None, *, spacing=4,
                emoji_size_factor: float = 1,
                emoji_position_offset=(0, 0)) -> typing.Tuple[int, int]:
        """
        Gets the size of the given text.
        :param text: The text to use.
        :param font: The font to use.
        :param spacing: The line spacing, in pixels.
        :param emoji_size_factor: The emoji resize factor.
        :param emoji_position_offset: The emoji's position offset.
        :return: A tuple with values width, height.
        """
        if not font:
            font = ImageFont.load_default()

        x, y = 0, 0
        nodes = get_nodes(text.split('\n'))

        for line in nodes:
            this_x = 0
            for node in line:
                content = node['content']
                width, _ = font.getsize(content)
                if node['type'] != 'text':
                    width = int(emoji_size_factor * font.size)

                this_x += width
            y += spacing + font.size
            if this_x > x:
                x = this_x

        return x, y - spacing



class BaseRequester:
    """
    The base requester that all requesters must inherit from.
    """
    BASE_URL = 'https://twemoji.maxcdn.com/v/latest/256x256/'
    BASE_DISCORD_URL = 'https://cdn.discordapp.com/emojis/'
    BASE_MICROSOFT_URL = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/320/microsoft/209/'
