import argparse

# and
class Conjunction:
    def __init__(self):
        self.children = []

    def __str__(self):
        res = ''
        for i, child in enumerate(self.children):
            if i == len(self.children) - 1:
                res += f'{str(child)}'
            else:
                res += f'{str(child)} and '

        return f'{res}'

# or
class Disjunction:
    def __init__(self):
        self.children = []

    def __str__(self):
        res = ''
        for i, child in enumerate(self.children):
            if i == len(self.children) - 1:
                res += f'{str(child)}'
            else:
                res += f'{str(child)} or '

        return f'{res}'

class Literal:
    def __init__(self, value):
        self.value = value
        self.name = None
        self.negated = None

        self.parse()

    def parse(self):
        if '-' in self.value:
            self.negated = True
            self.value = self.value.strip('-')

        self.name = self.value

    def __str__(self):
        if self.negated:
            return f'not {self.name}'
        else:
            return self.name

def _parser(formula):
    formula = formula.strip().replace(' ', '')
    conjunctions = formula.split('},')
    output = []

    for conjunction in conjunctions:
        disjunction = conjunction.strip().strip('{').strip('}').split(',')
        output.append(disjunction)

    _conjunction = Conjunction()
    for conjunction in output:
        _disjunction = Disjunction()
        for disjunction_literal in conjunction:
            _literal = Literal(disjunction_literal)
            _disjunction.children.append(_literal)

        _conjunction.children.append(_disjunction)

    return _conjunction

def main():
    parser = argparse.ArgumentParser("sat solver")

    parser.add_argument(
        'formula',
        nargs=argparse.REMAINDER,
        help='e.g. {{-a, b}, {-v, r, q}}',
    )

    args = parser.parse_args()
    formula = ' '.join(args.formula)
    parsed = _parser(formula)
    print(f'Solving: {parsed}')


if __name__ == "__main__":
    main()
