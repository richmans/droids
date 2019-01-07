#!/usr/bin/env python3
import os
from urllib.parse import unquote
print("HTTP/1.0 200 Found")
print("Content-Type: text/plain\n")
qry = unquote(os.environ["QUERY_STRING"])
print(os.popen('ls /www/users/'+qry).read())
