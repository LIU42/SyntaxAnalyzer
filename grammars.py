import json
import re
import collections


class Token:
    def __init__(self, lines, index, type, word):
        self.type = type
        self.word = word
        self.lines = lines
        self.index = index

    def __str__(self):
        return f'<{self.type},{self.word}>'

    def __eq__(self, token):
        if isinstance(token, Token):
            if self.type == 'identifiers' or self.type == 'constants':
                return self.type == token.type
            else:
                return self.type == token.type and self.word == token.word
        return False

    def __hash__(self):
        if self.type == 'identifiers' or self.type == 'constants':
            return hash(self.type)
        else:
            return hash(self.type) + hash(self.word)

    @property
    def is_end(self):
        return self.type == 'ends' and self.word == '#'

    @staticmethod
    def ends():
        return Token(0, 0, 'ends', '#')

    @staticmethod
    def load_full(content):
        match = re.match(r'<(.+?), (.+?), (.+?), (.*)>', content)

        lines = match.group(1)
        index = match.group(2)
        type = match.group(3)
        word = match.group(4)

        return Token(lines, index, type, word)

    @staticmethod
    def load_short(content):
        match = re.match(r'<(.+?),(.*)>', content)

        type = match.group(1)
        word = match.group(2)

        return Token(0, 0, type, word)

    @staticmethod
    def loads(contents):
        return [Token.load_full(content) for content in contents] + [Token.ends()]


class Formula:
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def __str__(self):
        return f'{self.source} -> {self.target_string}'

    def __len__(self):
        return len(self.target)

    def __eq__(self, formula):
        if not isinstance(formula, Formula):
            return False
        if self.source != formula.source:
            return False
        if self.target != formula.target:
            return False
        return True

    def __hash__(self):
        return hash(self.source) + sum(hash(element) for element in self.target)

    @property
    def target_string(self):
        return ' '.join(str(element) for element in self.target)

    @staticmethod
    def load_element(content):
        if content[0] == '<':
            return Token.load_short(content)
        else:
            return content

    @staticmethod
    def load(contents):
        source_contents, target_contents = contents.split(' -> ')

        return Formula(source_contents, [
            Formula.load_element(content) for content in target_contents.split()
        ])

    @staticmethod
    def loads(formula_contents):
        return [Formula.load(contents.strip()) for contents in formula_contents]


class Formulas:
    def __init__(self, formulas):
        self.formulas = formulas
        self.number_mapper = setup_number_mapper(formulas)
        self.source_mapper = setup_source_mapper(formulas)

    def __len__(self):
        return len(self.formulas)

    @property
    def list(self):
        return self.formulas

    def get_number(self, formula):
        try:
            return self.number_mapper[formula]
        except KeyError:
            return None

    def find_by_source(self, source):
        return self.source_mapper[source]


def setup_number_mapper(formulas):
    return {formula: index for index, formula in enumerate(formulas)}


def setup_source_mapper(formulas):
    source_mapper = collections.defaultdict(set)

    for formula in formulas:
        source_mapper[formula.source].add(formula)

    return source_mapper


def load_grammar_configs():
    with open('configs/grammar.json', 'r') as grammars:
        return json.load(grammars)


def load_message_configs():
    with open('configs/message.json', 'r') as messages:
        return json.load(messages)


grammar_configs = load_grammar_configs()
message_configs = load_message_configs()


def load_formulas():
    return Formulas(Formula.loads(grammar_configs['formulas']))


def load_messages():
    messages = message_configs['messages']
    defaults = message_configs['defaults']

    message_rules = collections.defaultdict(lambda: defaults)

    for message in messages:
        message_rules[Token.load_short(message['token'])] = message['message']

    return message_rules
