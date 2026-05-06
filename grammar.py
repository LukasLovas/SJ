import csv

from rules import RULES


class Grammar:
    EPSILON = "epsilon"
    EOF = "$"
    START_SYMBOL = "xmldokument"

    FOLLOW = {
        "xmldokument": (EOF,),
        "xmldecl": ("<",),
        "vernumb": ("?>",),
        "element": (EOF, "</"),
        "element_tail": (EOF, "</"),
        "element_content": ("</",),
        "endtag": (EOF, "</"),
        "name": (">", "/>"),
        "namestart": (">", "/>", ".", "-", "_", ":", "NUMBER", "LETTER"),
        "name_tail": (">", "/>"),
        "namechar": (">", "/>", ".", "-", "_", ":", "NUMBER", "LETTER"),
        "letter": (">", "</", "/>", ".", "-", "_", ":", "!", "@", "#", "NUMBER", "LETTER"),
        "number": ("?>", "."),
        "number_tail": ("?>", "."),
        "digit": ("?>", ">", "</", "/>", ".", "-", "_", ":", "!", "@", "#", "NUMBER", "LETTER"),
        "word": ("</",),
        "word_tail": ("</",),
        "char": ("</", ".", "-", "_", ":", "!", "@", "#", "NUMBER", "LETTER"),
    }

    def __init__(self):
        self.rules = RULES
        self.table = {}
        self.terminals = ()
        self.non_terminals = ()

    def is_terminal(self, symbol):
        return symbol in self.terminals

    def is_non_terminal(self, symbol):
        return symbol in self.non_terminals

    def rule(self, rule_id):
        return self.rules[rule_id]

    def load_table(self, file_name):
        with open(file_name, newline="", encoding="utf-8") as table_file:
            reader = csv.reader(table_file)
            first_row = next(reader)
            table_terminals = self.strip_values(first_row[1:])
            loaded_table = {}

            for row in reader:
                if self.row_is_empty(row):
                    continue

                non_terminal = row[0].strip()
                loaded_table[non_terminal] = {}

                for terminal, raw_value in zip(table_terminals, row[1:]):
                    value = raw_value.strip()
                    if value != "":
                        loaded_table[non_terminal][terminal] = int(value)

            self.table = loaded_table
            self.terminals = tuple(table_terminals)
            self.non_terminals = tuple(loaded_table.keys())

    def strip_values(self, values):
        stripped = []
        for value in values:
            stripped.append(value.strip())
        return stripped

    def row_is_empty(self, row):
        for value in row:
            if value.strip() != "":
                return False
        return True

    def print_table(self):
        print("\n".join(self.format_transition_table()))

    def format_transition_table(self):
        lines = []
        lines.append("Pravidla:")
        for rule_id in sorted(self.rules):
            left_side, production = self.rules[rule_id]
            if len(production) == 0:
                right_side = self.EPSILON
            else:
                right_side = " ".join(production)
            lines.append(str(rule_id).rjust(2, "0") + ": " + left_side + " -> " + right_side)

        return lines
