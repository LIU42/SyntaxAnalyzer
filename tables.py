import collections
import items
import grammars

from items import Item
from grammars import Token


class ActionOption:
    def __init__(self, option, number):
        self.option = option
        self.number = number

    def __str__(self):
        return f'{self.option}-{self.number}'

    @property
    def is_accept(self):
        return self.option == 'A'

    @property
    def is_shift(self):
        return self.option == 'S'

    @property
    def is_reduce(self):
        return self.option == 'R'

    @staticmethod
    def shift(number):
        return ActionOption(option='S', number=int(number))

    @staticmethod
    def reduce(number):
        return ActionOption(option='R', number=int(number))

    @staticmethod
    def accept():
        return ActionOption(option='A', number=0)

    @staticmethod
    def load(contents):
        option, number = contents.strip().split('-')

        if option == 'A':
            return ActionOption.accept()
        if option == 'S':
            return ActionOption.shift(number)
        if option == 'R':
            return ActionOption.reduce(number)


class DynamicTable:
    def __init__(self, default=None):
        self.elements = collections.defaultdict(lambda: collections.defaultdict(lambda: default))
        self.conflicts = []

    def __getitem__(self, location):
        row = location[0]
        col = location[1]
        return self.elements[row][col]

    @property
    def listed_elements(self):
        return [(row, col, value) for row, cols in self.elements.items() for col, value in cols.items()]


class TransformTable(DynamicTable):
    def __setitem__(self, location, target):
        source = location[0]
        symbol = location[1]

        if symbol in self.elements[source]:
            self.conflicts.append(TransformTable.conflicts_info(source, symbol, self.elements[source][symbol], target))
        else:
            self.elements[source][symbol] = target

    @staticmethod
    def conflicts_info(source, symbol, old_target, new_target):
        return f'transform conflicts at ({source}, {symbol}) old target: {old_target} new target: {new_target})\n'


class ActionTable(DynamicTable):
    def __setitem__(self, location, action):
        state = location[0]
        token = location[1]

        if token in self.elements[state]:
            self.conflicts.append(ActionTable.conflicts_info(state, token, self.elements[state][token], action))
        else:
            self.elements[state][token] = action

    def save(self):
        with open('builds/actions.txt', 'w') as actions:
            actions.writelines(ActionTable.contents(state, token, action) for state, token, action in self.listed_elements)

    def load(self):
        with open('builds/actions.txt', 'r') as actions:
            for contents in actions.readlines():
                contents = contents.strip().split()

                state = contents[0]
                token = contents[1]
                action = contents[2]

                self.elements[int(state)][Token.load_short(token)] = ActionOption.load(action)

    @staticmethod
    def contents(state, token, action):
        return f'{state} {token} {action}\n'

    @staticmethod
    def conflicts_info(state, token, old_action, new_action):
        return f'action conflicts at ({state}, {token}) old action: {old_action} new action: {new_action})\n'


class GotoTable(DynamicTable):
    def __setitem__(self, location, target):
        source = location[0]
        symbol = location[1]

        if symbol in self.elements[source]:
            self.conflicts.append(GotoTable.conflicts_info(source, symbol, self.elements[source][symbol], target))
        else:
            self.elements[source][symbol] = target

    def save(self):
        with open('builds/gotos.txt', 'w') as gotos:
            gotos.writelines(GotoTable.contents(source, symbol, target) for source, symbol, target in self.listed_elements)

    def load(self):
        with open('builds/gotos.txt', 'r') as gotos:
            for contents in gotos.readlines():
                contents = contents.strip().split()

                source = contents[0]
                symbol = contents[1]
                target = contents[2]

                self.elements[int(source)][symbol] = int(target)

    @staticmethod
    def contents(source, symbol, target):
        return f'{source} {symbol} {target}\n'

    @staticmethod
    def conflicts_info(source, symbol, old_target, new_target):
        return f'goto conflicts at ({source}, {symbol}) old target: {old_target} new target: {new_target}\n'


class ActionGotoTable:
    def __init__(self):
        self.actions = ActionTable()
        self.gotos = GotoTable()

    def save(self):
        self.actions.save()
        self.gotos.save()

    def load(self):
        self.actions.load()
        self.gotos.load()

    def action(self, state, token):
        try:
            return self.actions[state, token]
        except KeyError:
            return None

    def goto(self, source, symbol):
        try:
            return self.gotos[source, symbol]
        except KeyError:
            return None


def create_transforms(formulas):
    start_items = items.closure({Item(formulas.list[0], search_index=0, search_token=Token.ends())}, formulas)

    number_allocation = {start_items: 0}
    new_items_set = {start_items}

    transforms = TransformTable(default=None)

    while len(new_items_set) > 0:
        searchable_items_set = new_items_set.copy()
        new_items_set.clear()

        for searchable_items in searchable_items_set:
            for element in items.transform_elements(searchable_items):
                reachable_items = items.reachable_items(searchable_items, element, formulas)

                if reachable_items not in number_allocation:
                    new_items_set.add(reachable_items)
                    number_allocation[reachable_items] = len(number_allocation)

                transforms[number_allocation[searchable_items], element] = number_allocation[reachable_items]

    return number_allocation, transforms


def expend_number_allocation(number_allocation):
    for allocated_items, allocated_number in number_allocation.items():
        for allocated_item in allocated_items:
            yield allocated_item, allocated_number


def output_items(number_allocation):
    with open('builds/items.txt', 'w') as outputs:
        outputs.write(f'total count: {len(number_allocation)}\n')

        for item, number in expend_number_allocation(number_allocation):
            outputs.write(f'items: {number} {item}\n')


def output_conflicts(conflicts):
    with open('builds/conflicts.txt', 'w') as outputs:
        outputs.writelines(conflicts)


def build_tables(tables, formulas):
    number_allocation, transforms = create_transforms(formulas)

    for source, element, target in transforms.listed_elements:
        if isinstance(element, Token):
            tables.actions[source, element] = ActionOption.shift(target)
        else:
            tables.gotos[source, element] = target

    for item, number in expend_number_allocation(number_allocation):
        if item.search_finished:
            if item.formula == formulas.list[0] and item.search_token.is_end:
                option = ActionOption.accept()
            else:
                option = ActionOption.reduce(formulas.get_number(item.formula))

            tables.actions[number, item.search_token] = option

    output_items(number_allocation)
    output_conflicts(transforms.conflicts + tables.actions.conflicts + tables.gotos.conflicts)

    return tables


def build():
    build_tables(ActionGotoTable(), grammars.load_formulas()).save()


if __name__ == '__main__':
    build()
