from time import sleep
from . import validators


def process1(**kwargs):
    for i in range(1, 21):
        print(f"Process 1: {i}")
        sleep(0.5)


def process2(**kwargs):
    for i in range(1, 51):
        print(f"Process 2: {i}")
        sleep(0.25)


def process3(**kwargs):
    for i in range(1, 101):
        print(f"Process 3: {i}")
        sleep(0.125)


