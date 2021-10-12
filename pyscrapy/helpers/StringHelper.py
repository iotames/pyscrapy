import re


class StringHelper:

    @staticmethod
    def get_all_in(string: str, start='(', end=')') -> list:
        # r'[(](.*?)[)]'   r'[<](.*?)[>]'
        return re.findall('[' + start + '](.*?)[' + end + ']', string)

    @staticmethod
    def get_first_in(string: str, start='(', end=')'):
        return StringHelper.get_all_in(string, *start, *end)[0]


if __name__ == '__main__':
    num = StringHelper.get_all_in('All Reviews <228>', start='<', end='>')
    numm = StringHelper.get_first_in('All Reviews {22877}', start='{', end='}')
    print(numm)
    print(num[0])
