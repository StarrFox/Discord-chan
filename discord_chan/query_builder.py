from typing import Self








class Query:
    def __init__(self): ...

    def build(self) -> str: ...

    def add_condition(self, value: str, param: object) -> Self: ...

    def group_by(self, value: str) -> Self: ...

    def order_by(self, value: str, *, desc: bool = True) -> Self: ...

    def limit(self, value: int) -> Self: ...











