class Base:

    name = "spiders"

    @property
    def columns(self) -> list:
        return [
            {'name': 'id', 'attributes': {'title': 'ID', 'width': '80px'}},
            {'name': 'created_at', 'attributes': {'title': '创建时间', 'width': '150', 'sortable': True}}
        ]
