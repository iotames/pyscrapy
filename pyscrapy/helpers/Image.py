import requests


class Image:

    @staticmethod
    def save_image_by_url(url, path):
        r = requests.get(url)
        if r.status_code != 200:
            return False
        with open(path, 'wb') as f:
            f.write(r.content)
        return True
