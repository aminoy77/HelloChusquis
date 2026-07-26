# DEPRECATED: This module is not used. Consider removing.
import asyncio
import functools
from typing import Callable, Any


def make_async(func: Callable[..., Any]) -> Callable[..., Any]:
    """Envuelve una función síncrona para hacerla compatible con asyncio."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Si ya es corutina (async def), devolver directamente
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)

        # Si no, ejecutarla en threadpool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, func, *args, **kwargs)
        return result

    return wrapper
