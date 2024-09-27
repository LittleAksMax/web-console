from uuid import uuid4
from json import JSONDecodeError, loads as json_loads
from threading import Thread, Lock
from time import sleep
import sys
from websockets.asyncio.server import ServerConnection
from websockets import ConnectionClosed
from auth import Authenticator
from socketstdout import ThreadSafeEmittingStream


class WebSocketHandler:
    __AUTH = "AUTH"
    __SELECT = "SELECT"
    __DATA = "DATA"
    __QUIT = "QUIT"
    __MESSAGE_TIMEOUT = 0.1

    def __init__(self, authenticator: Authenticator, stream: ThreadSafeEmittingStream, processes: dict[str, tuple]):
        self.__auth = authenticator
        self.__stream = stream
        self.__conn = dict()
        self.__proc = processes

    @staticmethod
    async def __message(websocket: ServerConnection, stream: ThreadSafeEmittingStream, with_sleep=True) -> None:
        await websocket.send(stream.flush().decode("utf-8"))
        if with_sleep:
            sleep(WebSocketHandler.__MESSAGE_TIMEOUT)

    @staticmethod
    async def __get(websocket: ServerConnection) -> dict[str, any] | None:
        try:
            json_msg = json_loads(await websocket.recv())

            # json_msg should be a dictionary with fields, "type", "sid", and "data"
            if not isinstance(json_msg, dict) or len(json_msg) != 3 or "type" not in json_msg \
                    or "sid" not in json_msg or "data" not in json_msg:
                raise KeyError()

            if json_msg.get("type", None) not in \
                    [WebSocketHandler.__SELECT, WebSocketHandler.__AUTH, WebSocketHandler.__DATA]:
                raise ValueError()

            return json_msg
        except JSONDecodeError:
            await websocket.send("error: data should be valid JSON format\n")
            return None
        except KeyError:
            await websocket.send("error: data should contain only entries \"type\" and \"data\"\n")
            return None
        except ValueError:
            await websocket.send(f"error: \"type\" field should be \"{WebSocketHandler.__AUTH}\" or "
                                 f"\"{WebSocketHandler.__SELECT}\" or \"{WebSocketHandler.__DATA}\"")
            return None

    async def __get_invoked_process(self, websocket: ServerConnection, client_id: str) -> str | None:
        # get process
        event = await WebSocketHandler.__get(websocket)
        if event["type"] != WebSocketHandler.__SELECT:
            await websocket.send(f"error: message type should be \"{WebSocketHandler.__SELECT}\"\n")
            return None
        invoked_process = event["data"]
        if invoked_process == WebSocketHandler.__QUIT:
            print(f"Connection closed for client {client_id}")
            return None
        if invoked_process not in self.__proc:
            await websocket.send(f"error: invalid process invoked\n")
            return None
        return invoked_process

    async def __get_parameters(self, websocket: ServerConnection) -> dict[str, any] | None:
        event = await WebSocketHandler.__get(websocket)
        if event["type"] != WebSocketHandler.__DATA:
            await websocket.send(f"error: message type should be \"{WebSocketHandler.__DATA}\"\n")
            return None
        data = event["data"]
        if not isinstance(data, dict):
            await websocket.send(f"error: data for invoked process must be mapping (i.e., dictionary)\n")
            return None
        return data

    async def handle(self, websocket: ServerConnection) -> None:
        client_id = ""
        try:
            await websocket.send("Connection established\n")
            event = await WebSocketHandler.__get(websocket)
            if not event:
                return
            if event["type"] != WebSocketHandler.__AUTH:
                await websocket.send(f"error: message type should be \"{WebSocketHandler.__AUTH}\"\n")
                return

            key = event["data"]
            if not self.__auth.validate(key):
                await websocket.send("error: invalid authentication\n")
                return
            await websocket.send("Successfully authenticated\n")

            # generate new client ID and send to client to use in future communications
            client_id = uuid4().hex
            await websocket.send(f"Session ID: {client_id}\n")

            # event loop
            while True:
                # if there is already an existing session, use that thread and stream
                if client_id not in self.__conn:

                    # get name of invoked process
                    invoked_process = await self.__get_invoked_process(websocket, client_id)
                    if invoked_process is None:
                        return

                    # get corresponding process handler and validator
                    proc, validator = self.__proc.get(invoked_process, (None, None))
                    assert proc is not None and validator is not None

                    # try to extract data
                    data = await self.__get_parameters(websocket)
                    if data is None:
                        return

                    # validate retrieved data
                    err: list[str] = validator(**data)
                    if any(err):
                        # always send the first error in the list until all errors fixed
                        await websocket.send(f"error: " + "\nerror: ".join(err))
                        continue  # continue, not return, because we want to allow retries
                    # set up buffer, lock, and stream for process
                    buffer = bytearray()
                    buffer_lock = Lock()
                    stream = ThreadSafeEmittingStream(buffer, buffer_lock)

                    # create thread and start it with invoked process
                    proc_name = proc.__name__
                    thread = Thread(target=proc, kwargs=data, name=f"{proc_name}@{client_id}")

                    # set up session for running process
                    self.__conn[client_id] = (thread, stream)
                else:
                    thread, stream = self.__conn.pop(client_id)
                    print(f"Session rejoined for client {client_id}.")

                sys.stdout = stream

                # conditionally start thread, since it might have been recalled
                if not thread.is_alive():
                    thread.start()

                # keep messaging client while process runs
                while thread.is_alive():
                    await WebSocketHandler.__message(websocket, stream)
                # clear buffer if there is anything still left in it
                await WebSocketHandler.__message(websocket, stream, with_sleep=False)

                # once process is completed
                thread.join()
                sys.stdout = sys.__stdout__

                # destroy session after process terminates
                self.__conn.pop(client_id)
        except ConnectionClosed:
            print(f"Connection suddenly closed for client {client_id}")
        except KeyboardInterrupt:
            print(f"Connection closed manually.")
        finally:
            # reset stream
            sys.stdout = sys.__stdout__

            print(f"Handler terminated for client {client_id}")
