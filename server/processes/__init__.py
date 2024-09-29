"""
NOTE: processes have to do their own error handling
      - an exception will crash the whole thing if it is just let loose
        since the websocket handler does not handle the errors
"""


from time import sleep
from socketstdout import ThreadSafeEmittingStream
from . import validators
from random import uniform


def process1(stream: ThreadSafeEmittingStream, **kwargs):
    stream.write("Script started")

    for i in range(1, 21):
        stream.write(f"Process 1: {i}")
        sleep(0.5)

    stream.write("Script finished")


def process2(stream: ThreadSafeEmittingStream, **kwargs):
    stream.write("Script started")
    for i in range(1, 51):
        stream.write(f"Process 2: {i}")
        sleep(0.25)

    stream.write("Script finished")


def process3(stream: ThreadSafeEmittingStream, **kwargs):
    stream.write("Script started")

    for i in range(1, 101):
        stream.write(f"Process 3: {i}")
        sleep(0.125)

    stream.write("Script finished")


def long_process(stream: ThreadSafeEmittingStream, **kwargs):
    stream.write("Script started")

    for i in range(1, 100):
        stream.write(".", end="")
        sleep(uniform(0.5, 2))

    stream.write("Script finished")
