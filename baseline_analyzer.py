import logging
from packet_analyzer import PacketAnalyzer


class BaselineAnalyzer(PacketAnalyzer):
    def analyze_session(self, packets, proto='TCP'):
        tcp = packets[0][proto]
        dst = tcp.dport
        logging.debug("{} packets to destination port {}".format(len(packets),dst))
        convo = self.packets_to_convo(packets)
        self.baseline.addConvo(dst, convo)

    def banner(self):
        return "==== IDS Baseline Creation ===="