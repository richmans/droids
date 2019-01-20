import logging
from packet_analyzer import PacketAnalyzer
from anomaly import Anomaly
from util import printable


class DetectionAnalyzer(PacketAnalyzer):
    def __init__(self):
        super().__init__()
        self.anomalies = []

    def analyze_session(self, packets, proto='TCP'):
        tcp = packets[0][proto]
        dst = tcp.dport
        logging.debug("{} packets to destination port {}".format(len(packets),dst))
        convo = self.packets_to_convo(packets)
        message, score = self.baseline.checkConvo(dst, convo)
        if score > 0.1:
            self.anomalies.append(Anomaly(*convo, dst, message, score))
            logging.warning(message)

    def banner(self):
        return "==== IDS Anomaly detection ===="

    def render_report(self):
        result = "====  IDS Anomaly report  ====\n"
        for a in self.anomalies:
            result += "=== Anomaly on port: {:>5} ===\n".format(a.dst)
            result += "Problem: {}\n".format(a.message)
            result += "Score: {:.2}\n".format(a.score)
            result += "<<< recv\n"
            result += printable(a.recv)
            result += ">>> sent\n"
            result += printable(a.sent)
            result += "===------------------------===\n"
        return result