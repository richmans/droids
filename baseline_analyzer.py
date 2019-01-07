from util import full_duplex
from baseline import Baseline
import logging
from collections import Counter
from scapy.all import Raw


class BaselineError(Exception):
    pass


class BaselineAnalyzer:
    def __init__(self):
        self.baseline = Baseline()
        self.mymac = None

    def load_baseline(self, infil):
        self.baseline = Baseline.read(infil)

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
        logging.debug("Determined my mac: {}, {}/{}".format(self.mymac, common[0][1], common[1][1]))
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
        if self.target == 'baseline':
            self.baseline.addConvo(dst, convo)
        elif self.target == 'detection':
            message, score = self.baseline.checkConvo(dst, convo)
            if score > 0.1:
                logging.warning(message)

    def packets_to_convo(self, packets):
        sent = b''.join([self.get_payload(p) for p in packets if self.my_packet(p)])
        recv = b''.join([self.get_payload(p) for p in packets if not self.my_packet(p)])
        return (sent, recv)

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

    def run(self, packets, target='baseline', mymac=None):
        if target == 'baseline':
            logging.info("==== IDS Baseline Creation ====")
        elif target == 'detection':
            logging.info("==== IDS Anomaly detection ====")
        else:
            raise BaselineError("Unknown analyzer target")
        self.target = target
        if mymac:
            self.mymac = mymac
        else:
            self.find_my_mac(packets)
        sessions = packets.sessions(full_duplex)
        logging.info('Read {} packets in {} sessions'.format(len(packets), len(sessions)))
        for s in sessions:
            packets = sessions[s]
            self.analyze_session(packets, s)
        return self.baseline
