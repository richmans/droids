from copy import copy
from difflib import SequenceMatcher
from ascii import RED, GREEN, RESET
from util import dbg, printable



class TemplateError(Exception):
    pass


class ConvoTemplate:
    def __init__(self, sent, recv, baseline=None):
        self.recv = Template(recv, baseline=baseline)
        self.sent = Template(sent, baseline=baseline)
        self.baseline = baseline

    def similarity(self, sent, recv):
        sim_sent = self.sent.similarity(sent)
        sim_recv = self.recv.similarity(recv)
        return (sim_sent + sim_recv) / 2.0

    def update(self, sent, recv):
        self.sent.update(sent)
        self.recv.update(recv)

    def show(self):
        result = "<<< recv\n" + self.recv.show() + "\n"
        result += ">>> sent\n" + self.sent.show() + "\n"
        result += "----------\n"
        return result

    def dict(self):
        result = {'sent': self.sent.dict(), 'recv': self.recv.dict()}
        return result

    def load(i, b=None):
        result = ConvoTemplate("","", b)
        result.sent =  Template.load(i['sent'], b)
        result.recv = Template.load(i['recv'], b)
        return result


class Template:
    def __init__(self, text, variables=[], baseline=None):
        self.text = text
        self.baseline = baseline
        self.variables = variables
        self.consolidate_vars()

    def fit_variable(self, var):
        for own_var in self.variables:
            if own_var.fits(var):
                return True
        return False

    def calculate_length_penalty(self, vars):
        if len(self.text) == 0:
            return 0.0
        my_ratio = sum(v.len for v in self.variables) / len(self.text)
        other_ratio = sum(v.len for v in vars) / len(self.text)
        return abs(other_ratio - my_ratio)

    def calculate_growth_penalty(self, vars):
        my_ratio = sum(v.max_len - v.len for v in self.variables) / len(self.text)
        other_ratio = sum(v.max_len - v.len for v in vars) / len(self.text)
        return abs(other_ratio - my_ratio)

    def calculate_shrink_penalty(self, vars):
        my_ratio = sum(v.len - v.min_len for v in self.variables) / len(self.text)
        other_ratio = sum(v.len - v.min_len for v in vars) / len(self.text)
        return abs(other_ratio - my_ratio)

    def score_variables(self, vars):
        dbg("SCORING")
        if all(self.fit_variable(v) for v in vars):
            return 1.0
        score =  1.0
        score -= self.calculate_length_penalty(vars)
        dbg('len', score)
        score -= self.calculate_growth_penalty(vars)
        dbg('gro', score)
        score -= self.calculate_shrink_penalty(vars)
        dbg('shri', score)
        return max(0, score)

    def get_special_chars(self, text):
        if self.baseline is None:
            return set()
        result = {c for c in self.baseline.special_strings if c in text}
        return result

    def find_variables(self, other):
        vars = []
        s = SequenceMatcher(None, self.text, other)
        for tag, i1, i2, j1, j2 in s.get_opcodes():
            ln = i2-i1
            ln2 = j2-j1
            s2 = other[j1:j2]
            specials = self.get_special_chars(s2)
            if tag == 'replace':
                vars.append(TemplateVariable(i1, ln, min(ln2, ln), max(ln2, ln), specials))
            elif tag == 'delete':
                vars.append(TemplateVariable(i1, ln, 0, ln))
            elif tag == 'insert':
                vars.append(TemplateVariable(i1, 0, 0, ln2, specials))
        return vars

    def similarity(self, other):
        vars = self.find_variables(other)
        return self.score_variables(vars)

    def update(self, other):
        vars = self.find_variables(other)
        for v in vars:
            if not self.fit_variable(v):
                self.variables.append(v)
        self.consolidate_vars()

    def consolidate_vars(self):
        old_vars = sorted(self.variables)
        new_vars = []
        pos = 0
        dbg("CONSOLIDATING", old_vars)
        for v in old_vars:
            if v.pos >= pos or pos == 0:
                dbg("APPEND", v)
                new_vars.append(v)
            else:
                dbg("MERGE", v)
                new_vars[-1].merge(v)
            pos = max(pos, v.pos + v.len)
        self.variables = new_vars

    def show(self):
        pos = 0
        result = ""
        printable_text = printable(self.text)
        for var in self.variables:
            result += printable_text[pos:var.pos]
            if var.len == 0:
                result += RED + '*' + RESET
            else:
                result += GREEN + printable_text[var.pos:var.pos + var.len] + RESET
            pos = max(pos, var.pos + var.len)
        result += printable_text[pos:]
        return result

    def dict(self):
        result = {"text": self.text}
        result['variables'] = [v.dict() for v in self.variables]
        return result

    def load(i, b=None):
        vars = [TemplateVariable.load(v) for v in i['variables']]
        return Template(i['text'], vars, b)


class TemplateVariable:
    def __init__(self, pos, len, min_len, max_len, special_strings=set()):
        self.pos = pos
        self.len = len
        self.min_len = min_len
        self.max_len = max_len
        self.special_strings = copy(special_strings)

    def fits(self, other):
        if not isinstance(other, TemplateVariable):
            return False
        return self.pos <= other.pos and \
            other.pos + other.len <= self.pos + self.len and \
            other.max_len <= self.max_len and \
            other.min_len >= self.min_len and \
            other.special_strings - self.special_strings == set()

    def merge(self, other):
        if other.pos < self.pos:
            raise TemplateError("Can't merge variable with variable at a lower pos")
        self.len = max((other.pos + other.len) - self.pos, self.len)
        self.max_len = max(self.max_len, other.pos + other.max_len - self.pos)
        self.min_len = min(self.min_len, other.pos + other.min_len - self.pos)
        self.special_strings |= other.special_strings

    def __eq__(self, other):
        if not isinstance(other, TemplateVariable):
            return False
        return self.pos == other.pos and \
            self.len == other.len and \
            self.min_len == other.min_len and \
            self.max_len == other.max_len and \
            self.special_strings == other.special_strings

    def dict(self):
        return {"pos": self.pos, 'len': self.len, 'min_len': self.min_len, 'max_len': self.max_len, 'special_strings': self.special_strings}

    def load(i):
        return TemplateVariable(i['pos'], i['len'], i['min_len'], i['max_len'], i['special_strings'])

    def __repr__(self):
        return "var: {}:{} R{}-{} S[{}]".format(self.pos, self.len, self.min_len, self.max_len, ''.join(self.special_strings))

    def __lt__(self, other):
        return other.pos > self.pos
