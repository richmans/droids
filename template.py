from copy import copy
from difflib import SequenceMatcher
from ascii import RED, GREEN, RESET
from util import dbg, printable
from util import ConfigMixin


class TemplateError(Exception):
    pass


class ConvoTemplate(ConfigMixin):
    def __init__(self, sent, recv, config={}):
        self.recv = Template(recv, [], config)
        self.sent = Template(sent, [], config)
        self.config = config

    def similarity(self, sent, recv):
        sim_sent = self.sent.similarity(sent)
        sim_recv = self.recv.similarity(recv)
        return min(sim_sent, sim_recv)

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

    def load(i, config=None):
        result = ConvoTemplate("","", config)
        result.sent =  Template.load(i['sent'],config)
        result.recv = Template.load(i['recv'], config)
        return result


class Template(ConfigMixin):
    def __init__(self, text, variables=[], config={}):
        if type(text) == str:
            text = text.encode()
        self.text = text
        self.config = config
        self.variables = variables
        self.special_strings = self.get_config('special_strings', {})
        self.consolidate_vars()

    def fit_variable(self, var):
        for own_var in self.variables:
            if own_var.fits(var):
                return True
        return False

    def calculate_length_penalty(self, other):
        if len(self.text) == 0:
            if len(other) == 0:
                return 0.0
            else:
                return 1.0

        difference = abs(len(self.text) - len(other))
        return min(1.0, difference / len(self.text))

    def calculate_var_len_penalty(self, vars):
        other_sum = sum(v.len for v in vars)
        if len(self.text) == 0 and other_sum > 0:
            return 1
        if len(self.text) == 0 and other_sum == 0:
            return 0
        my_ratio = sum(v.len for v in self.variables) / len(self.text)
        other_ratio = sum(v.len for v in vars) / len(self.text)
        return abs(other_ratio - my_ratio)

    def calculate_growth_penalty(self, vars):
        other_sum = sum(v.max_len - v.len for v in vars)
        if len(self.text) == 0 and other_sum > 0:
            return 1
        if len(self.text) == 0 and other_sum == 0:
            return 0
        my_ratio = sum(v.max_len - v.len for v in self.variables) / len(self.text)
        other_ratio = sum(v.max_len - v.len for v in vars)  / len(self.text)
        return abs(other_ratio - my_ratio)

    def calculate_shrink_penalty(self, vars):
        if len(self.text) == 0:
            return 0
        my_ratio = sum(v.len - v.min_len for v in self.variables) / len(self.text)
        other_ratio = sum(v.len - v.min_len for v in vars) / len(self.text)
        return abs(other_ratio - my_ratio)

    def calculate_ratio_penalty(self, other):
        matcher =  self.get_matcher(other)
        return 1.0 - matcher.ratio()

    def calculate_specials_penalty(self, vars):
        my_specials = set()
        for v in self.variables:
            my_specials.update(v.special_strings)
        other_specials = set()
        for v in vars:
            other_specials.update(v.special_strings)
        penalties = sum(v for s,v in self.special_strings.items() if s in other_specials and not s in my_specials)
        return penalties

    def score_difference(self, other_vars, other):
        if all(self.fit_variable(v) for v in other_vars):
            return 1.0
        score = 1.0
        penalties = list()
        penalties.append(self.calculate_length_penalty(other) * self.get_config('score_length_weight',0))
        penalties.append(self.calculate_var_len_penalty(other_vars) *  self.get_config('score_vlen_weight',0))
        penalties.append(self.calculate_growth_penalty(other_vars) *  self.get_config('score_growth_weight',0))
        penalties.append(self.calculate_shrink_penalty(other_vars) *  self.get_config('score_shrink_weight',0))
        penalties.append(self.calculate_ratio_penalty(other) *  self.get_config('score_ratio_weight',0))
        penalties.append(self.calculate_specials_penalty(other_vars) *  self.get_config('score_specials_weight',0))
        score -= sum(penalties)
        return max(0.0, score)

    def get_special_chars(self, text):
        result = {c for c in self.special_strings if c in text}
        return result

    def get_matcher(self, other):
        other_text = other
        max_text_len = self.get_config('max_text_len', 1024)
        if len(other_text) >  max_text_len:
            other_text = other[:max_text_len]
        my_text = self.text
        if len(my_text) > max_text_len:
            my_text = max_text_len
        s = SequenceMatcher(None, my_text, other_text, autojunk=False)
        return s

    def find_variables(self, other):
        if type(other) == str:
            other = other.encode()
        vars = []
        matcher = self.get_matcher(other)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            ln = i2-i1
            ln2 = j2-j1
            s2 = other[j1:j2]
            s1 = self.text[i1:i2]
            specials = self.get_special_chars(s2) | self.get_special_chars(s1)
            if tag == 'replace':
                vars.append(TemplateVariable(i1, ln, min(ln2, ln), max(ln2, ln), specials))
            elif tag == 'delete':
                vars.append(TemplateVariable(i1, ln, 0, ln))
            elif tag == 'insert':
                vars.append(TemplateVariable(i1, 0, 0, ln2, specials))
        return vars

    def similarity(self, other):
        if type(other) == str:
            other = other.encode()
        vars = self.find_variables(other)
        score =  self.score_difference(vars, other)
        return score

    def update(self, other):
        if type(other) == str:
            other = other.encode()
        vars = self.find_variables(other)
        for v in vars:
            if not self.fit_variable(v):
                self.variables.append(v)
        self.consolidate_vars()

    def consolidate_vars(self):
        if self.variables == []:
            return
        old_vars = sorted(self.variables)
        new_vars = []
        pos = 0
        for v in old_vars:
            if v.pos > pos or len(new_vars) == 0:
                new_vars.append(v)
            else:
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
            other.pos + other.max_len <= self.pos + self.max_len and \
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
        return "var: {}:{} R{}-{} S[{}]".format(self.pos, self.len, self.min_len, self.max_len, b''.join(self.special_strings).decode())

    def __lt__(self, other):
        return other.pos > self.pos
