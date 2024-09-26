"""
NOTE: processes have to do their own error handling
      - an exception will crash the whole thing if it is just let loose
        since the websocket handler does not handle the errors
"""


from time import sleep
from . import validators
from random import uniform


def process1(**kwargs):
    print("Script started")

    for i in range(1, 21):
        print(f"Process 1: {i}")
        sleep(0.5)

    print("Script finished")


def process2(**kwargs):
    print("Script started")
    for i in range(1, 51):
        print(f"Process 2: {i}")
        sleep(0.25)

    print("Script finished")


def process3(**kwargs):
    print("Script started")

    for i in range(1, 101):
        print(f"Process 3: {i}")
        sleep(0.125)

    print("Script finished")


def long_process(**kwargs):
    print("Script started")

    for i in range(1, 100):
        print(".", end="")
        sleep(uniform(0.5, 2))

    print("Script finished")
