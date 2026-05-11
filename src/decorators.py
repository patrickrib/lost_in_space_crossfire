from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def safe_asset_loader(
    default: T | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T | None]]:
    def decorator(func: Callable[..., T]) -> Callable[..., T | None]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T | None:
            try:
                return func(*args, **kwargs)
            except FileNotFoundError as exc:
                print(f"Aviso de asset: {exc}")
                return default
            except Exception as exc:
                print(f"Aviso de asset: não foi possível carregar o asset: {exc}")
                return default

        return wrapper

    return decorator
