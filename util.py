from scapy.all import TCP, IP, ICMP, UDP, ARP
import os
from string import printable as printable_chars
import re


def dbg(*msg):
    if 'DEBUG' in os.environ:
        print(*msg)
    

# https://gist.github.com/MarkBaggett/d8933453f431c111169158ce7f4e2222
# scapy helper for session analysis
def full_duplex(p):
    sess = "Other"
    if 'Ether' in p:
        if 'IP' in p:
            if 'TCP' in p:
                sess = str(sorted(["TCP", p[IP].src, p[TCP].sport, p[IP].dst, p[TCP].dport],key=str))
            elif 'UDP' in p:
                sess = str(sorted(["UDP", p[IP].src, p[UDP].sport, p[IP].dst, p[UDP].dport] ,key=str))
            elif 'ICMP' in p:
                sess = str(sorted(["ICMP", p[IP].src, p[IP].dst, p[ICMP].code, p[ICMP].type, p[ICMP].id] ,key=str))
            else:
                sess = str(sorted(["IP", p[IP].src, p[IP].dst, p[IP].proto] ,key=str))
        elif 'ARP' in p:
            sess = str(sorted(["ARP", p[ARP].psrc, p[ARP].pdst],key=str))
        else:
            sess = p.sprintf("Ethernet type=%04xr,Ether.type%")
    return sess

def printable(input):
    return ''.join([chr(x) if chr(x) in printable_chars else '.' for x in input])


def is_printable(input):
    return all(chr(x) in printable_chars for x in input)

class ConfigMixin:
    def get_config(self, name, default=None):
        if not hasattr(self, 'config'):
            raise Exception("No config")
        if name in self.config:
            return self.config[name]
        return default

def scrubbed_equals(text, other):
    flag_p = re.compile(b'FLAG{[0-9A-F]+}')
    text = text.strip()
    other = other.strip()
    text = flag_p.sub(b'FLAG{XXX}', text)
    other = flag_p.sub(b'FLAG{XXX}', other)
    return text == other