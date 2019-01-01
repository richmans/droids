from template import ConvoTemplate
import logging


class Baseline:
    TRAINING_TRESHOLD = 0.7

    def __init__(self):
        self.ports = {}

    def addConvo(self, port, convo):
        if port not in self.ports:
            self.ports[port] = PortBaseline(port)
        self.ports[port].addConvo(convo)

    def show(self):
        logging.info("***** BASELINE *****")
        for port, baseline in self.ports.items():
            print(baseline)


class PortBaseline:
    def __init__(self, port):
        self.port = port
        self.templates = []

    def __str__(self):
        return "Port: {:<5}: {} templates".format(self.port, len(self.templates))

    def addConvo(self, convo):
        # if convo matches existing template, update it. else add a new template
        found_template = False
        for temp in self.templates:
            if temp.similarity(*convo) > Baseline.TRAINING_TRESHOLD:
                found_template = True
                temp.update(*convo)
                break
        if not found_template:
            self.templates.append(ConvoTemplate(*convo))
