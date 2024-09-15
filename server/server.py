import sys
import asyncio
from websockets.asyncio.server import serve
from threading import Thread, Lock
from time import sleep
from json import JSONDecodeError, loads as json_loads, dumps as json_dumps
from processes import process1, process2, process3
from processes.validators import process1_validator, process2_validator, process3_validator
from socketstdout import EmittingStream

# delay in seconds between ticks in the handler
TICK_DELAY = 0.1

# easy way to call validators and processes
CALLS = dict(
    process1=(process1, process1_validator),
    process2=(process2, process2_validator),
    process3=(process3, process3_validator)
)


async def handler(websocket):
    while True:
        invoked_process = await websocket.recv()

        # ensure the process to invoke is in the dictionary
        if invoked_process not in CALLS:
            await websocket.close(1003, f"No process called {invoked_process}.\n")
            return
        
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
            await websocket.close(1003, f"The received parameters are not in valid JSON format. {parameters}\n")
            return

        # validate and quit if there are any errors
        errors = validator(**parameters)
        if any(errors):
            await websocket.close(1003, f"The data could not be validated: {json_dumps(errors)}\n")
            return

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
    async with serve(handler, "0.0.0.0", 3000):
        await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    asyncio.run(main())
