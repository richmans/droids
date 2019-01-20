class Anomaly:
    def __init__(self, sent, recv, dst, message, score):
        self.recv = recv
        self.sent = sent
        self.message = message
        self.score = score
        self.dst = dst