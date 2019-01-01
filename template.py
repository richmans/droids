import logging
from difflib import SequenceMatcher


class ConvoTemplate:
    def __init__(self, recv, sent):
        self.recv = Template(recv)
        self.sent = Template(sent)

    def similarity(self, sent, recv):
        sim_sent = self.sent.similarity(sent)
        sim_recv = self.recv.similarity(recv)
        return (sim_sent + sim_recv) / 2.0

    def update(self, sent, recv):
        self.sent.update(sent)
        self.recv.update(recv)

class Template:
    def __init__(self, text, variables=[]):
        self.text = text
        self.variables = variables

    def score_variables(self, vars):
        return 1.0

    def find_variables(self, other):
        vars = []
        s = SequenceMatcher(None, self.text, other)
        for tag, i1, i2, j1, j2 in s.get_opcodes():
            ln = i2-i1
            ln2 = j2-j1
            s = [self.text[i1:i2], other[j1:j2]]
            if tag == 'replace':
                vars.append(TemplateVariable(i1, ln, ln, s))
            elif tag == 'delete':
                vars.append(TemplateVariable(i1, 0, ln, s))
            elif tag == 'insert':
                vars.append(TemplateVariable(i1, 0, ln2, s))
        return vars

    def similarity(self, other):
        vars = self.find_variables(other)
        return self.score_variables(vars)

    def update(self, other):
        vars = self.find_variables(other)


class TemplateVariable:
    def __init__(self, pos, min_len, max_len, contents):
        self.pos = pos
        self.min_len = min_len
        self.max_len = max_len
        self.contents = contents
