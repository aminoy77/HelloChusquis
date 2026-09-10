# Python asyncio module

- In Python, `async def` coroutines run on an event loop started by `asyncio.run(main())`.
- In Python, `await` yields control until the awaited coroutine completes.
- In Python, `asyncio.gather(a(), b())` runs coroutines concurrently and collects results.
- In Python, `asyncio.create_task(coro())` schedules background work returning a Task handle.
- In Python, `asyncio.sleep(n)` pauses cooperatively without blocking the loop.
- In Python, `asyncio.wait_for(coro(), timeout)` cancels overrun work with TimeoutError.
- In Python, `asyncio.Queue` coordinates producer-consumer pipelines between coroutines.
- In Python, `asyncio.Lock` and `asyncio.Semaphore` bound shared access and concurrency.
- In Python, `asyncio.to_thread(fn)` offloads blocking calls so the loop stays responsive.
- In Python, never call blocking IO directly in coroutines; await async libraries instead.
