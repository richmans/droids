from util import scrubbed_equals

class Anomaly:
    def __init__(self, sent, recv, dst, message, score):
        self.recv = recv
        self.sent = sent
        self.message = message
        self.score = score
        self.dst = dst



    def __eq__(self, other):
        if type(other) != Anomaly:
            return False
        return scrubbed_equals(other.sent, self.sent) and scrubbed_equals(other.recv, self.recv)

    def __lt__(self, other):
        return self.score < other.score
