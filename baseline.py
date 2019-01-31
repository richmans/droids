from template import ConvoTemplate
import logging
import yaml
from util import ConfigMixin

class Baseline(ConfigMixin):
    TRAINING_TRESHOLD = 0.4
    DETECTION_TRESHOLD = 0.1
    SPECIAL_STRINGS = {b'?':0.1,b';':0.3,b'%':0.3,b'\'':0.1,b'"':0.3,b'/':0.1,b'\\':0.1,b'..':0.3,b'`':0.3,b'{':0.1, b'(':0.1,b'FLAG': 1.0}

    def __init__(self):
        self.ports = {}
        self.config = {
            'unrecognized_port': 0.5,
            'nonmatching_convo': 0,
            'max_text_len': 1024,
            'score_length_weight': 0.3,
            'score_vlen_weight': 0.3,
            'score_growth_weight': 0.2,
            'score_shrink_weight': 0.2,
            'score_ratio_weight': 0.3,
            'score_specials_weight': 1.0,
            'training_treshold': Baseline.TRAINING_TRESHOLD,
            'detection_treshold':  Baseline.DETECTION_TRESHOLD,
            'special_strings': Baseline.SPECIAL_STRINGS
        }


    def addConvo(self, port, convo):
        if port not in self.ports:
            self.ports[port] = PortBaseline(port, self.config)
        self.ports[port].addConvo(convo)

    def checkConvo(self, port, convo):
        if port not in self.ports:
            return ('Conversation on port {} was not recognized.'.format(port), self.get_config('unrecognized_port'))
        score = max(0, 1-self.ports[port].checkConvo(convo))
        logging.debug("Convo matching score {}".format(score))
        if score > self.get_config('detection_treshold', 0.5):
            return ('Conversation on port {} did not match conversations in the baseline. Best matching score was {:.2f}'.format(port, 1-score), score)
        return ('No anomalies detected', 0.0)

    def show(self):
        logging.info("***** BASELINE *****")
        for port, baseline in self.ports.items():
            print(baseline)

    def dict(self):
        result = {}
        result['config'] = self.config
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
        result.config = i['config']
        for p, port in i['ports'].items():
            result.ports[p] = PortBaseline.load(port, result.config)
        return result


class PortBaseline(ConfigMixin):
    def __init__(self, port, config=None):
        self.port = port
        self.templates = []
        self.config = config

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

    def load(i, conf=None):
        result = PortBaseline(i['port'], conf)
        result.templates = [ConvoTemplate.load(c, conf) for c in i['templates']]
        return result

    def checkConvo(self, convo):
        score = max([t.similarity(*convo) for t in self.templates] + [0])
        return score

    def addConvo(self, convo):
        # if convo matches existing template, update it. else add a new template
        best_score = 0
        best_temp = None
        for temp in self.templates:
            temp_score = temp.similarity(*convo)
            if temp_score > best_score:
                best_score = temp_score
                best_temp = temp
        if best_score > self.get_config('training_treshold'):
            best_temp.update(*convo)
        else:
            self.templates.append(ConvoTemplate(*convo, self.config))
