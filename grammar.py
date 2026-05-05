class Grammar:
    EPSILON = "epsilon"
    EOF = "EOF"
    START_SYMBOL = "xmldokument"

    TERMINALS = (
        "<?xml",
        "version=",
        "?>",
        ".",
        "<",
        ">",
        "</",
        "-",
        ":",
        "_",
        "/>",
        "LETTER",
        "NUMBER",
        "!",
        "@",
        "#",
        EOF,
    )

    NON_TERMINALS = (
        "xmldokument",
        "xmldecl",
        "vernumb",
        "element",
        "element_tail",
        "element_content",
        "endtag",
        "name",
        "namestart",
        "name_tail",
        "namechar",
        "letter",
        "number",
        "number_tail",
        "digit",
        "word",
        "word_tail",
        "char",
    )

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
        self.table = self.create_default_table()

    def create_default_table(self):
        name_start = ("LETTER", "_", ":")
        name_char = ("LETTER", "NUMBER", ".", "-", "_", ":")
        word_start = ("LETTER", "NUMBER", ".", "-", "_", ":", "!", "@", "#")

        table = {
            "xmldokument": {
                "<?xml": ["xmldecl", "element"],
                "<": ["element"],
            },
            "xmldecl": {
                "<?xml": ["<?xml", "version=", "vernumb", "?>"],
            },
            "vernumb": {
                "NUMBER": ["number", ".", "number"],
            },
            "element": {
                "<": ["<", "name", "element_tail"],
            },
            "element_tail": {
                "/>": ["/>"],
                ">": [">", "element_content", "endtag"],
            },
            "element_content": {
                "<": ["element"],
                "</": [],
            },
            "endtag": {
                "</": ["</", "name", ">"],
            },
            "name": {},
            "namestart": {
                "LETTER": ["letter"],
                "_": ["_"],
                ":": [":"],
            },
            "name_tail": {
                ">": [],
                "/>": [],
            },
            "namechar": {
                "LETTER": ["letter"],
                "NUMBER": ["digit"],
                ".": ["."],
                "-": ["-"],
                "_": ["_"],
                ":": [":"],
            },
            "letter": {
                "LETTER": ["LETTER"],
            },
            "number": {
                "NUMBER": ["digit", "number_tail"],
            },
            "number_tail": {
                "NUMBER": ["number"],
                "?>": [],
                ".": [],
            },
            "digit": {
                "NUMBER": ["NUMBER"],
            },
            "word": {},
            "word_tail": {
                "</": [],
            },
            "char": {
                "LETTER": ["letter"],
                "NUMBER": ["digit"],
                ".": ["."],
                "-": ["-"],
                "_": ["_"],
                ":": [":"],
                "!": ["!"],
                "@": ["@"],
                "#": ["#"],
            },
        }

        for lookahead in name_start:
            table["name"][lookahead] = ["namestart", "name_tail"]
        for lookahead in name_char:
            table["name_tail"][lookahead] = ["namechar", "name_tail"]
        for lookahead in word_start:
            table["element_content"][lookahead] = ["word"]
            table["word"][lookahead] = ["char", "word_tail"]
            table["word_tail"][lookahead] = ["word"]

        return table

    def is_terminal(self, symbol):
        return symbol in self.TERMINALS

    def is_non_terminal(self, symbol):
        return symbol in self.NON_TERMINALS

    def load_table(self, file_name):
        loaded_table = self.create_default_table()
        with open(file_name, "r", encoding="utf-8") as table_file:
            line_number = 0
            for raw_line in table_file:
                line_number += 1
                line = raw_line.strip()
                if line == "" or line.startswith("#"):
                    continue
                if "=" not in line or "," not in line.split("=", 1)[0]:
                    raise ValueError("Invalid table line " + str(line_number) + ": " + raw_line)

                left_side, right_side = line.split("=", 1)
                non_terminal, lookahead = left_side.split(",", 1)
                non_terminal = non_terminal.strip()
                lookahead = lookahead.strip()

                if not self.is_non_terminal(non_terminal):
                    raise ValueError("Unknown non-terminal: " + non_terminal)
                if not self.is_terminal(lookahead):
                    raise ValueError("Unknown terminal: " + lookahead)

                right_side = right_side.strip()
                if right_side == "" or right_side == self.EPSILON:
                    loaded_table[non_terminal][lookahead] = []
                else:
                    loaded_table[non_terminal][lookahead] = right_side.split()

        self.table = loaded_table

    def print_table(self):
        print("\nPrechodova tabulka:")
        for non_terminal in self.NON_TERMINALS:
            if non_terminal in self.table:
                for terminal in self.table[non_terminal]:
                    production = self.table[non_terminal][terminal]
                    if len(production) == 0:
                        right_side = self.EPSILON
                    else:
                        right_side = " ".join(production)
                    print(non_terminal + ", " + terminal + " = " + right_side)
