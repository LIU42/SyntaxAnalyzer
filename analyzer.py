import grammars

from grammars import Token
from tables import ActionGotoTable


class SyntaxError:
    def __init__(self, token, message):
        self.token = token
        self.message = message

    def __str__(self):
        return f'Error at {self.token.lines}:{self.token.index} `{self.token.word}`: {self.message}'


class SyntaxAnalyzer:
    def __init__(self):
        self.tables = ActionGotoTable()
        self.tables.load()
        self.formulas = grammars.load_formulas()
        self.messages = grammars.load_messages()
        self.tokens = []
        self.errors = []
        self.symbol_stack = []
        self.states_stack = []
        self.index = 0
        self.analysis_finished = False

    @property
    def reached_end(self):
        return self.index >= len(self.tokens)

    @property
    def finished(self):
        return self.analysis_finished or self.reached_end

    @property
    def symbol(self):
        return self.symbol_stack[-1]

    @property
    def state(self):
        return self.states_stack[-1]

    @property
    def token(self):
        return self.tokens[self.index]

    def analysis_process(self):
        action_option = self.tables.action(self.state, self.token)

        if action_option is None:
            self.errors.append(SyntaxError(self.token, self.messages[self.token]))
            self.index += 1

            while not self.reached_end and self.tables.action(self.state, self.token) is None:
                self.index += 1

        elif action_option.is_accept:
            self.analysis_finished = True

        elif action_option.is_shift:
            self.symbol_stack.append(self.token)
            self.states_stack.append(action_option.number)
            self.index += 1

        elif action_option.is_reduce:
            reduce_formula = self.formulas.list[action_option.number]

            del self.symbol_stack[-len(reduce_formula):]
            del self.states_stack[-len(reduce_formula):]

            goto_state = self.tables.goto(self.state, reduce_formula.source)

            if goto_state is None:
                self.errors.append(SyntaxError(self.token, self.messages[self.token]))
                self.analysis_finished = True
            else:
                self.states_stack.append(goto_state)
                self.symbol_stack.append(reduce_formula.source)

    def analysis(self, tokens):
        self.tokens = tokens
        self.errors = []
        self.symbol_stack = [Token.ends()]
        self.states_stack = [0]
        self.index = 0
        self.analysis_finished = False

        while not self.finished:
            self.analysis_process()

        return self.errors
