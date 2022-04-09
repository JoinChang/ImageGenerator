import requests
import typing
import unicodedata
from io import BytesIO
from ..classes import BaseRequester


__all__ = [
    'Requester'
]


class Requester(BaseRequester):
    """
    Makes requests to fetch images using requests.
    Use `AsyncRequester` for asynchronous requests.
    """
    def __init__(self, *, session: typing.Optional[requests.Session] = None, _microsoft=False):
        self.session: requests.Session = session or requests.Session()
        self.cache: typing.Dict[str, bytes] = {}
        self._microsoft = _microsoft

    def _request(self, url) -> typing.Optional[BytesIO]:
        if url in self.cache:
            return BytesIO(self.cache[url])

        with self.session.get(url, proxies={"http": None, "https": None}) as response:
            if response.status_code == 200:
                content = response.content
                stream = BytesIO(content)
                self.cache[url] = content
                return stream

    def get_twemoji(self, unicode: str) -> typing.Optional[BytesIO]:
        """
        Returns a stream of the given unicode emoji.
        :param unicode: The unicode emoji.
        :return: The bytes stream of that emoji.
        """
        hex_code = format(ord(unicode[0]), 'x')
        if not self._microsoft:
            url = self.BASE_URL + hex_code + '.png'
        else:
            name = unicodedata.name(unicode, hex_code)
            name = name.lower().replace(' ', '-')
            url = self.BASE_MICROSOFT_URL + name + f'_{hex_code}.png'
        return self._request(url)

    def get_discord_emoji(self, emoji_id: typing.Union[int, str]) -> typing.Optional[BytesIO]:
        """
        Returns a stream of the given Discord emoji.
        :param emoji_id: The emoji's ID.
        :return: A bytes stream of the emoji.
        """
        url = self.BASE_DISCORD_URL + str(emoji_id) + '.png?v=1'
        return self._request(url)

    def close(self):
        """
        Closes the requests session.
        This will also delete the cache as it will become pointless.
        """
        self.session.close()
        del self.session
        del self.cache

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
