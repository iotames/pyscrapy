class Response:

    @staticmethod
    def data(data: dict, msg='success', code=200):
        response = {"code": code, "data": data, "msg": msg}
        return response

    @staticmethod
    def success(data: dict, msg='success'):
        return Response.data(data, msg)

    @staticmethod
    def error(msg='error', code=400, data=None):
        if data is None:
            data = {}
        return Response.data(data, msg, code)
