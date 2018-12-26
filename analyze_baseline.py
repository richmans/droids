from argparse import ArgumentParser
from scapy.all import *
from os.path import isfile
import sys
import logging
from collections import Counter
from binascii import hexlify

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

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

class Baseline:
    TRAINING_TRESHOLD = 0.7

    def __init__(self):
        self.ports = {}

    def addConvo(self, port, convo):
        if port not in self.ports:
            self.ports[port] = PortBaseLine(port)
        self.ports[port].addConvo(convo)

class PortBaseline:
    def __init__(self, port):
        self.port = port
        self.templates = []

    def addConvo(self, convo):
        # if convo matches existing template, update it. else add a new template
        found_template = False
        for temp in self.templates:
            if temp.similarity(convo) > Baseline.TRAINING_TRESHOLD:
                found_template = True
                temp.update(convo)
                break
        if not found_template:
            self.templates.append(ConvoTemplate(convo))

class ConvoTemplate:
    def __init__(self, recv, sent):
        self.recv = Template(recv)
        self.sent = Template(sent)

    def similarity(self, other):
        sim_sent = self.sent.similarity(other.sent)
        sim_recv = self.recv.similarity(other.recv)
        return (sim_sent + sim_recv) / 2.0

    def update(self, other):
        self.sent.update(other.sent)
        self.recv.update(other.recv)

class Template:
    def __init__(self, text, variables=[]):
        self.text = text
        self.variables = variables

    def similarity(self, other):
        return 0.0

    def update(self, other):
        pass

class TemplateVariable:
    pass

class BaselineAnalyzer:
    def __init__(self):
        self.baseline = Baseline()
        self.mymac = None

    def find_my_mac(self, packets):
        src_macs = [p['Ether'].src for p in packets if 'Ether' in p]
        dst_macs = [p['Ether'].dst for p in packets if 'Ether' in p]
        c = Counter(src_macs + dst_macs)
        common =  c.most_common(2)
        if len(common) < 2:
            raise Exception("Could not determine my mac address... Try giving me more packets!")
        if common[0][1] < common[1][1]:
            raise Exception("Could not determine my mac address... Try giving me more packets!")
        self.mymac = common[0][0]
        logging.debug("Determined my mac: " + self.mymac)
        return self.mymac

    def my_packet(self, packet):
        if 'Ether' not in packet:
            logging.debug("Can not analyze packet that has no ether")
            return
        eth = packet['Ether']
        from_me = False
        if eth.src == self.mymac:
            from_me = True
        return from_me

    def get_payload(self, packet, proto='TCP'):
        if 'Raw' in packet:
            return packet[Raw].load
        else:
            return b''

    def analyze_tcp_session(self, s, packets):
        tcp = packets[0]['TCP']
        dst = tcp.dport
        logging.debug("{} packets to destination port {}".format(len(packets),dst))
        convo = self.packets_to_convo(packets)

    def analyze_udp_session(self, packets):
        pass

    def analyze_icmp_session(self, packets):
        pass

    def analyze_session(self, packets, s):
        logging.debug('Examining session {} containing {} packets'.format(s, len(packets)))
        if self.my_packet(packets[0]):
            logging.debug("First packet is from me, ignoring session")
        elif len(packets) < 2:
            logging.debug("Not enough packets in this session")
        elif 'IP' not in packets[0]:
            logging.debug("Session is not in ipv4 :-()")
        elif 'TCP' in packets[0]:
            self.analyze_tcp_session(s, packets)
        elif 'UDP' in packets[0]:
            self.analyze_udp_session(packets)
        elif 'ICMP' in packets[0]:
            self.analyze_icmp_session(packets)
        else:
            logging.debug("Unrecognized protocol :(")

    def create_baseline(self, packets):
        logging.info("==== IDS Baseline Creation ====")
        self.find_my_mac(packets)
        sessions = packets.sessions(full_duplex)
        logging.info('Read {} packets in {} sessions'.format(len(packets), len(sessions)))
        for s in sessions:
            packets = sessions[s]
            self.analyze_session(packets, s)

    def show(self):
        logging.info("***** BASELINE *****")
        for port, convo in self.ports.items():
            print("Port: {:10s}".format(port))
            inp = convo['recv']
            inbytes = sum(len(p) for p in inp)
            outp = convo['sent']
            outbytes = sum(len(p) for p in outp)
            print("Packets In: {} Out: {}".format(len(inp), len(outp)))
            print("Bytes In: {} Out: {}".format(inbytes, outbytes))

def read_pcap(pcap):
    logging.info("Loading pcap {}".format(pcap))
    if not isfile(pcap):
        logging.error("Could not find pcap file {}".format(pcap))
    packets = rdpcap(pcap)
    logging.debug("Pcap {} succesfuly loaded with {} packets".format(pcap, len(packets)))
    return packets

def read_pcaps(pcap):
    if type(pcap) == list:
        packets = reduce((lambda l, p: l+p), [read_pcap(p) for p in pcap])
    else:
        packets = read_pcap(pcap)
    return packets

def error(message):
    logging.error(message)
    sys.exit(1)

def main():
    parser = ArgumentParser(description='Process some integers.')
    parser.add_argument('cmd', type=str, choices=['baseline'])
    parser.add_argument('pcap',  nargs='+',help='Read a pcap for analysis')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    if args.cmd == 'baseline':
        packets = read_pcaps(args.pcap)
        analyzer = BaselineAnalyzer()
        analyzer.create_baseline(packets)
        analyzer.show()

if __name__ == '__main__':
    main()
