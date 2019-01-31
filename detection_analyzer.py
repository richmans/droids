import logging
from packet_analyzer import PacketAnalyzer
from anomaly import Anomaly
from util import printable


class DetectionAnalyzer(PacketAnalyzer):
    def __init__(self):
        super().__init__()
        self.trunc_messages = 1024
        self.anomalies = []

    def analyze_session(self, packets, proto='TCP'):
        tcp = packets[0][proto]
        dst = tcp.dport
        logging.debug("{} packets to destination port {}".format(len(packets),dst))
        convo = self.packets_to_convo(packets)
        if not convo:
            return
        message, score = self.baseline.checkConvo(dst, convo)
        if score > 0.1:
            self.anomalies.append(Anomaly(*convo, dst, message, score))
            logging.warning(message)
        else:
            logging.debug("Session matches the baseline.")

    def post_analysis(self):
        anom = []
        for a in self.anomalies:
            if a not in anom:
                anom.append(a)

        self.anomalies = sorted(anom, reverse=True)

    def banner(self):
        return "==== IDS Anomaly detection ===="

    def render_report(self):
        result = "====  IDS Anomaly report  ====\n"
        result+= "Found {} anomalies\n".format(len(self.anomalies))
        for a in self.anomalies:
            recv = a.recv
            sent = a.sent
            if self.trunc_messages and len(recv) > self.trunc_messages:
                recv = recv[:self.trunc_messages] + b'\n...[snip]\n'
            if self.trunc_messages and len(sent) > self.trunc_messages:
                sent = sent[:self.trunc_messages]+ b'\n...[snip]\n'
            result += "=== Anomaly on port: {:>5} ===\n".format(a.dst)
            result += "Problem: {}\n".format(a.message)
            result += "Score: {:.2}\n".format(a.score)
            result += "<<< recv\n"
            result += printable(recv)
            result += "\n>>> sent\n"
            result += printable(sent)
            result += "\n===------------------------===\n"
        return result