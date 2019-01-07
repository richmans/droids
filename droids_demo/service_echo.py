#!/usr/bin/env python3
while True:
    try:
        lin = input()
    except EOFError:
        break
    if lin == 'give-me-flag!':
        print("FLAG{ABCCIDIEIEJEEJEJJJBJGJIEJIEJBIJ}")
    else:
        print(lin)
