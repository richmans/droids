#!/usr/bin/env python3
import subprocess
import sys
from select import select
from fcntl import fcntl, F_GETFL, F_SETFL
from os import O_NONBLOCK
import re


def filter_traffic(is_input, message):
    check_message = message.strip()
    if check_message == 'give-me-flag!':
        return "NO FLAG FOR YOUU\n"
    message = message.replace("fido", 'fidodido')
    return message


args = sys.argv[1:]

process = subprocess.Popen(args, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
inputs = [process.stderr, sys.stdin, process.stdout]

flags = fcntl(sys.stdin, F_GETFL)
fcntl(sys.stdin, F_SETFL, flags | O_NONBLOCK)
flags = fcntl(process.stdin, F_GETFL)
fcntl(process.stdin, F_SETFL, flags | O_NONBLOCK)
flags = fcntl(process.stdout, F_GETFL)
fcntl(process.stdout, F_SETFL, flags | O_NONBLOCK)
flags = fcntl(process.stderr, F_GETFL)
fcntl(process.stderr, F_SETFL, flags | O_NONBLOCK)

while process.poll() is None:
    readable, _, _ = select(inputs, (), ())
    if process.stdout in readable:
        message = process.stdout.read().decode()
        message = filter_traffic(False, message)
        sys.stdout.write(message)
        sys.stdout.flush()
    elif process.stderr in readable:
        message = process.stderr.read().decode()
        message = filter_traffic(False, message)
        sys.stderr.write(message)
        sys.stderr.flush()
    elif sys.stdin in readable:
        message = sys.stdin.read()
        if message == '':
            process.stdin.close()
            inputs.remove(sys.stdin)
        else:
            message = filter_traffic(False, message).encode()
            process.stdin.write(message)
            process.stdin.flush()

sys.exit(process.returncode)
#print("Proc exit: {}".format(process.returncode))