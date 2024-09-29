import os
import asyncio
from websockets.asyncio.server import serve
from threading import Thread, Lock
from processes import process1, process2, process3, long_process
from processes.validators import process1_validator, process2_validator, \
    process3_validator, long_process_validator
from socketstdout import ThreadSafeEmittingStream
from auth import Authenticator
from handler import WebSocketHandler

# delay in seconds between ticks in the handler
TICK_DELAY = 0.1

# easy way to call validators and processes
CALLS = dict(
    process1=(process1, process1_validator),
    process2=(process2, process2_validator),
    process3=(process3, process3_validator),
    long_process=(long_process, long_process_validator)
)

# this dictionary contains active connections, it should be
CONN_KEY = "auth"
CONNECTIONS: dict[str, tuple[bytearray, Lock, Thread]] = {}


async def main():
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        raise KeyError('missing environment variable SECRET_KEY')
    authenticator = Authenticator(secret_key)
    stream = ThreadSafeEmittingStream(bytearray(), Lock())
    ws_handler = WebSocketHandler(authenticator, stream, CALLS)
    async with serve(ws_handler.handle, "0.0.0.0", 3000):
        await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    asyncio.run(main())
