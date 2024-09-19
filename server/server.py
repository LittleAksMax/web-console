import sys
import os
import asyncio
from websockets.asyncio.server import serve, ServerConnection
from threading import Thread, Lock
from time import sleep
from json import JSONDecodeError, loads as json_loads, dumps as json_dumps
from processes import process1, process2, process3
from processes.validators import process1_validator, process2_validator, process3_validator
from socketstdout import EmittingStream
from auth import Authenticator

# delay in seconds between ticks in the handler
TICK_DELAY = 0.1

# easy way to call validators and processes
CALLS = dict(
    process1=(process1, process1_validator),
    process2=(process2, process2_validator),
    process3=(process3, process3_validator)
)

# this dictionary contains active connections, it should be 
CONNECTIONS = {}


async def handler(websocket: ServerConnection, authenticator: Authenticator):
    # we need to authenticate this connection
    # the first message should be a secret key that is hashed
    authentication_message_hash_bytes = await websocket.recv(decode=False)
    if not authenticator.validate(authentication_message_hash_bytes):
        await websocket.send("error: invalid authentication message")
        await websocket.close()
        return
    else:
        await websocket.send("Successfully authenticated")

    while True:
        invoked_process = await websocket.recv()

        # ensure the process to invoke is in the dictionary
        if invoked_process not in CALLS:
            await websocket.send(f"error: no process called {invoked_process}.\n")
            continue
        
        await websocket.send(f"Received process: {invoked_process}\n")
        # unpack relevant process function and validator function
        proc, validator = CALLS[invoked_process]

        # receive JSON data and validate format of JSON
        json_parameters = await websocket.recv()
        parameters = dict()
        try:
            parameters = json_loads(json_parameters)
            await websocket.send(f"Received parameters: {json_parameters}\n")
        except JSONDecodeError:
            await websocket.send(f"error: received parameters are not in valid JSON format. {parameters}\n")
            continue

        # validate and quit if there are any errors
        errors = validator(**parameters)
        if any(errors):
            await websocket.send(f"error: data could not be validated: {json_dumps(errors)}\n")
            continue

        # create thread to run process in parallel
        buffer = bytearray('', 'utf-8')
        buffer_lock = Lock()  # lock used to access buffer between threads
        sys.stdout = EmittingStream(buffer, buffer_lock)
        thread = Thread(target=proc, kwargs=parameters)
        await websocket.send("Script started\n")

        thread.start()

        # while the process is running
        while thread.is_alive():
            with buffer_lock:
                await websocket.send(buffer.decode('utf-8'))
                buffer.clear()
            sleep(TICK_DELAY)

        # make sure we send whatever remains as well
        with buffer_lock:
            await websocket.send(buffer.decode('utf-8'))
            buffer.clear()

        await websocket.send("Script finished\n")
        # join thread once it has completed
        thread.join()
        sys.stdout = sys.__stdout__


async def main():
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        raise KeyError('missing environment variable SECRET_KEY')
    authenticator = Authenticator(secret_key)
    async with serve(lambda ws: handler(ws, authenticator), "0.0.0.0", 3000):
        await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    # TODO: list of active connections and threads on 'connection' event
    # TODO: authenticating on 'upgrade' event
    asyncio.run(main())
