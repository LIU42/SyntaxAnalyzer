from grammars import Token


class Item:
    def __init__(self, formula, search_index, search_token):
        self.formula = formula
        self.search_index = search_index
        self.search_token = search_token

    def __str__(self):
        return f'{self.formula}, {self.search_index}, {self.search_token}'

    def __eq__(self, item):
        if not isinstance(item, Item):
            return False
        if self.formula != item.formula:
            return False
        if self.search_index != item.search_index:
            return False
        if self.search_token != item.search_token:
            return False
        return True

    def __hash__(self):
        return hash(self.formula) + hash(self.search_index) + hash(self.search_token)

    @property
    def search_finished(self):
        return self.search_index >= len(self.formula)

    @property
    def current_element(self):
        try:
            return self.formula.target[self.search_index]
        except IndexError:
            return None

    @property
    def next_element(self):
        try:
            return self.formula.target[self.search_index + 1]
        except IndexError:
            return None

    @property
    def closure_enable(self):
        return not self.search_finished and isinstance(self.current_element, str)

    @staticmethod
    def ends(formula):
        return Item(formula, 0, Token.ends())

    @staticmethod
    def next(item):
        return Item(item.formula, item.search_index + 1, item.search_token)


def subsets(element, formulas, excepts):
    for formula in filter(lambda formula: formula.target[0] not in excepts, formulas.find_by_source(element)):
        yield first_set(formula.target[0], formulas, excepts)


def first_set(element, formulas, excepts=None):
    if isinstance(element, Token):
        return {element}

    if excepts is None:
        current_excepts = {element}
    else:
        current_excepts = excepts.union({element})

    return {token for subset in subsets(element, formulas, current_excepts) for token in subset}


def generate_closure_items(item, formulas):
    for formula in formulas.find_by_source(item.current_element):
        if next_element := item.next_element:
            search_set = first_set(next_element, formulas)
        else:
            search_set = {item.search_token}

        for search_token in search_set:
            yield Item(formula, search_index=0, search_token=search_token)


def new_closure_items(item, closure, formulas):
    return {item for item in generate_closure_items(item, formulas) if item not in closure}


def closure(items, formulas):
    items_closure = items.copy()
    new_items = items.copy()

    while len(new_items) > 0:
        await_items = filter(lambda item: item.closure_enable, new_items.copy())
        new_items.clear()

        for item in await_items:
            new_items = new_items.union(new_closure_items(item, items_closure, formulas))

        items_closure = items_closure.union(new_items)

    return frozenset(items_closure)


def transform_elements(items):
    return {element for item in items if (element := item.current_element)}


def goto(items, element):
    return {Item.next(item) for item in items if item.current_element == element}


def reachable_items(items, element, formulas):
    return closure(goto(items, element), formulas)
