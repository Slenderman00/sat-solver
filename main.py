import argparse
import copy

# and
class Conjunction:
    def __init__(self):
        self.children = []
        self.unit_clauses = []
        self.backtracing_clauses = []
        self._stack = []

    def get_all(self):
        population = []
        for child in self.children:
            if not child.always_true:
                population.append(child.get_all())
        return population

    def get_falsifiable_children(self):
        return [child for child in self.children if not child.always_true]

    def remove_tautologies(self):
        self.children = self.get_falsifiable_children()

    def clean(self):
        self.remove_tautologies()
        for child in self.children:
            child.remove_false_children()

    def prune(self):
        for child in self.children:
            child.simplify()

    def process_unit_clauses(self):
        self.unit_clauses = []
        for child in self.children:
            if child.is_unit_clause():
                child.set_value(True)
                child.check_values()
                self.unit_clauses.append(child.children[0])
        self.propagate_clauses(self.unit_clauses)

    def _pick_clause_index(self):
        for i, child in enumerate(self.children):
            if not getattr(child, "always_true", False) and len(child.children) > 0:
                return i
        return None

    def backtracing(self):
        idx = self._pick_clause_index()
        if idx is None:
            return
        self._stack.append({"snap": copy.deepcopy(self), "idx": idx, "flipped": False})
        self.backtracing_clauses = []
        chosen = self.children[idx].set_value_return_literal(True)
        self.backtracing_clauses.append(chosen)
        self.propagate_clauses(self.backtracing_clauses)

    def try_flip_last(self):
        while self._stack:
            frame = self._stack[-1]
            if not frame["flipped"]:
                restored = copy.deepcopy(frame["snap"])
                self.__dict__ = restored.__dict__
                frame["flipped"] = True
                self.backtracing_clauses = []
                idx = frame["idx"]
                if idx is None or idx >= len(self.children) or getattr(self.children[idx], "always_true", False) or len(self.children[idx].children) == 0:
                    idx = self._pick_clause_index()
                    frame["idx"] = idx
                    if idx is None:
                        return True
                chosen = self.children[idx].set_value_return_literal(False)
                self.backtracing_clauses.append(chosen)
                self.propagate_clauses(self.backtracing_clauses)
                return True
            else:
                self._stack.pop()
        return False

    def propagate_clauses(self, clauses):
        for child in self.children:
            child.propagate_clauses(clauses)

    def find_conflict(self):
        return any(getattr(l, "conflict", False) for l in self.unit_clauses + self.backtracing_clauses)

    def check_values(self):
        for child in self.children:
            child.check_values()

    def __str__(self):
        res = ''
        for i, child in enumerate(self.children):
            if i == len(self.children) - 1:
                res += f'{str(child)}'
            else:
                res += f'{str(child)}, '
        return f'{{{res}}}'

# or
class Disjunction:
    def __init__(self):
        self.children = []
        self.always_true = False

    def get_all(self):
        return self.children

    def get_falsifiable_children(self):
        return [child for child in self.children if child.value is True or child.value is None]

    def remove_false_children(self):
        self.children = self.get_falsifiable_children()

    def is_unit_clause(self):
        return len(self.children) == 1

    def set_value(self, value):
        for child in self.children:
            child.set_value(value ^ child.negated)

    def set_value_return_literal(self, value):
        self.children[0].set_value(value ^ self.children[0].negated)
        return self.children[0]

    def simplify(self):
        for child in self.children:
            for other in self.children:
                if child.is_negative_of(other):
                    self.always_true = True

    def check_values(self):
        for child in self.children:
            if child.value:
                self.always_true = True
                return True

    def propagate_clauses(self, clauses):
        for child in self.children:
            child.propagate_clauses(clauses)

    def __str__(self):
        if self.always_true:
            return '{True}'
        res = ''
        for i, child in enumerate(self.children):
            if i == len(self.children) - 1:
                res += f'{str(child)}'
            else:
                res += f'{str(child)}, '
        return f'{{{res}}}'

class Literal:
    def __init__(self, name):
        self.variable_value = None
        self.name = name
        self.negated = False
        self.conflict = False
        self.parse()

    @property
    def value(self):
        if self.variable_value is None:
            return None
        return not self.variable_value if self.negated else self.variable_value

    def set_value(self, value):
        self.variable_value = value

    def is_negative_of(self, other):
        if other.name == self.name and other.negated != self.negated:
            return True
        return False

    def propagate_clauses(self, clauses):
        for literal in clauses:
            if literal == self:
                if (self.variable_value is not None and self.variable_value != literal.variable_value):
                    self.conflict = True
                    return
                self.variable_value = literal.variable_value

    def parse(self):
        n = self.name.strip()
        if n.startswith('-'):
            self.negated = True
            n = n[1:]
        self.name = n

    def __str__(self):
        if self.value is not None:
            return 'True' if self.value else 'False'
        return f'-{self.name}' if self.negated else self.name

    def __eq__(self, other):
        return self.name == other.name

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
    parser = argparse.ArgumentParser("SAT Solver")
    parser.add_argument(
        'formula',
        nargs=argparse.REMAINDER,
        help='e.g. {{-a, b}, {-v, r, q}}',
    )
    args = parser.parse_args()
    formula = ' '.join(args.formula)
    parsed = _parser(formula)
    print("Solving:")
    print(parsed)
    print("=" * 50)
    # Start solving
    while True:
        print("Current Formula:")
        print(parsed)
        print("-" * 50)
        # Prune the formula
        parsed.prune()
        print("After Pruning:")
        print(parsed)
        print("-" * 50)
        # Clean after pruning
        parsed.clean()
        print("After Cleaning (Post-Pruning):")
        print(parsed)
        print("-" * 50)
        # Process unit clauses
        parsed.process_unit_clauses()
        print("After Processing Unit Clauses:")
        if parsed.find_conflict():
            # try flipping some decision before UNSAT
            if parsed.try_flip_last():
                print("After Flipping Last Decision:")
                print(parsed)
                print("-" * 50)
                continue
            print("UNSATISFIABLE!")
            break
        print(parsed)
        print("-" * 50)
        # Clean after processing unit clauses
        parsed.clean()
        print("After Cleaning (Post-Unit Clauses):")
        print(parsed)
        print("-" * 50)
        # Check values
        parsed.check_values()
        print("After Checking Values:")
        print(parsed)
        print("-" * 50)
        # Clean after checking values
        parsed.clean()
        print("After Cleaning (Post-Checking Values):")
        print(parsed)
        print("-" * 50)
        # Check for termination conditions
        if not parsed.children:
            print("SATISFIABLE!")
            break
        if any(len(child.children) == 0 for child in parsed.children):
            if parsed.try_flip_last():
                print("After Flipping Last Decision:")
                print(parsed)
                print("-" * 50)
                continue
            print("UNSATISFIABLE!")
            break
        # Perform backtracking (decision)
        parsed.backtracing()
        print("After Backtracking:")
        if parsed.find_conflict():
            if parsed.try_flip_last():
                print("After Flipping Last Decision:")
                print(parsed)
                print("-" * 50)
                continue
            print("UNSATISFIABLE!")
            break
        print(parsed)
        print("-" * 50)
        # Clean after backtracking
        parsed.clean()
        print("After Cleaning (Post-Backtracking):")
        print(parsed)
        print("-" * 50)

if __name__ == "__main__":
    main()
