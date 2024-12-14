import hashlib


def get_md5(input_string: str) -> str:
    md5_hash = hashlib.md5()
    md5_hash.update(input_string.encode('utf-8'))
    # return hashlib.md5(to_bytes(input_string)).hexdigest()
    return md5_hash.hexdigest()