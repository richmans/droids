from template import ConvoTemplate
import logging
import yaml

class Baseline:
    TRAINING_TRESHOLD = 0.7
    DETECTION_TRESHOLD = 0.1

    def __init__(self):
        self.ports = {}
        self.training_treshold = Baseline.TRAINING_TRESHOLD
        self.detection_treshold = Baseline.DETECTION_TRESHOLD
        self.scores = {
            'unrecognized_port': 0.5,
            'nonmatching_convo': 0
        }

    def addConvo(self, port, convo):
        if port not in self.ports:
            self.ports[port] = PortBaseline(port)
        self.ports[port].addConvo(convo)

    def checkConvo(self, port, convo):
        if port not in self.ports:
            return ('Conversation on port {} was not recognized.'.format(port), self.scores['unrecognized_port'])
        score = max(0, 1-self.ports[port].checkConvo(convo))
        logging.debug("Convo matching score {}".format(score))
        if score > self.detection_treshold:
            return ('Conversation on port {} did not match conversations in the baseline. Best matching score was {:.2f}'.format(port, 1-score), score)
        return ('No anomalies detected', 0.0)

    def show(self):
        logging.info("***** BASELINE *****")
        for port, baseline in self.ports.items():
            print(baseline)

    def dict(self):
        result = {}
        result['training_treshold'] = self.training_treshold
        port_dict = {}
        for portbl in self.ports.values():
            port_dict[portbl.port] = portbl.dict()
        result['ports'] = port_dict
        return result

    def write(self, outfilname):
        if not outfilname:
            logging.error("Please specify a baseline file with --baseline")
            return
        try:
            logging.info("Writing to " + outfilname)
            with open(outfilname, 'w') as f:
                yaml.dump(self.dict(), f)
        except IOError:
            logging.error("Can't write to file " + outfilname)

    def read(infilname):
        if not infilname:
            logging.error("Please specify a baseline file with --baseline")
            return None
        try:
            logging.info("Reading from " + infilname)
            with open(infilname) as f:
                return Baseline.load(yaml.load(f))
        except IOError:
            logging.error("Can't read from file " + infilname)

    def load(i):
        result = Baseline()
        result.training_treshold = i['training_treshold']
        for p, port in i['ports'].items():
            result.ports[p] = PortBaseline.load(port)
        return result


class PortBaseline:
    def __init__(self, port):
        self.port = port
        self.templates = []

    def __str__(self):
        result = "***************\nPort: {:<5}: {} templates\n".format(self.port, len(self.templates))
        for i, temp in enumerate(self.templates):
            result += 'template {}\n'.format(i + 1)
            result += temp.show()
        result += "***************"
        return result

    def dict(self):
        result = {'port': self.port}
        result['templates'] = [t.dict() for t in self.templates]
        return result

    def load(i):
        result = PortBaseline(i['port'])
        result.templates = [ConvoTemplate.load(c) for c in i['templates']]
        return result

    def checkConvo(self, convo):
        score = max([t.similarity(*convo) for t in self.templates] + [0])
        return score

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
