
class Uri:

    @staticmethod
    def get_url(url: str, base_url: str) -> str:
        if url.startswith('http'):
            return url
        if url.startswith('/'):
            return base_url + url
        return base_url + '/' + url

