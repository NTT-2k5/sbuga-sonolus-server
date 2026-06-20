from typing import TypeVar

T = TypeVar("T")


def list_to_pages(data: list[T], items_per_page: int) -> list[list[T]]:
    return [data[i : i + items_per_page] for i in range(0, len(data), items_per_page)]
