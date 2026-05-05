from grammar import Grammar
from token import ErrorLog, Token


class Tokenizer:
    def __init__(self, source, recovery):
        self.source = source
        self.recovery = recovery
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        self.diagnostics = []
        self.fixed_tokens = (
            ("<?xml", "<?xml"),
            ("version=", "version="),
            ("?>", "?>"),
            ("</", "</"),
            ("/>", "/>"),
            ("<", "<"),
            (">", ">"),
            (".", "."),
            ("-", "-"),
            (":", ":"),
            ("_", "_"),
            ("!", "!"),
            ("@", "@"),
            ("#", "#"),
        )

    def tokenize(self):
        while self.position < len(self.source):
            if self.source[self.position].isspace():
                self.advance_position(self.source[self.position])
                continue

            token = self.next_token()
            if token is not None:
                self.tokens.append(token)
                continue

            bad_token = self.make_token("ERROR", self.source[self.position])
            message = "unexpected character " + repr(self.source[self.position])
            if self.recovery == "panic":
                skipped = self.panic_skip()
                self.diagnostics.append(
                    ErrorLog("LEX", message + "; skipped " + repr(skipped), bad_token)
                )
            else:
                self.diagnostics.append(ErrorLog("LEX", message, bad_token))
                break

        self.tokens.append(Token(Grammar.EOF, "", self.line, self.column, self.position))
        return self.tokens

    def next_token(self):
        for token_type, value in self.fixed_tokens:
            if self.source.startswith(value, self.position):
                return self.build_token_and_advance(token_type, value)

        character = self.source[self.position]
        if self.is_ascii_letter(character):
            return self.build_token_and_advance("LETTER", character)
        if character.isdigit():
            return self.build_token_and_advance("NUMBER", character)
        return None

    def is_ascii_letter(self, character):
        return ("A" <= character <= "Z") or ("a" <= character <= "z")

    def starts_token(self):
        for _token_type, value in self.fixed_tokens:
            if self.source.startswith(value, self.position):
                return True
        character = self.source[self.position]
        return self.is_ascii_letter(character) or character.isdigit()

    def build_token_and_advance(self, token_type, value):
        token = self.make_token(token_type, value)
        self.advance_position(value)
        return token

    def make_token(self, token_type, value):
        return Token(token_type, value, self.line, self.column, self.position)

    def advance_position(self, value):
        for character in value:
            self.position += 1
            if character == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1

    def panic_skip(self):
        start = self.position
        while self.position < len(self.source):
            if self.source[self.position].isspace():
                break
            if self.starts_token():
                break
            self.advance_position(self.source[self.position])
        if self.position == start:
            self.advance_position(self.source[self.position])
        return self.source[start:self.position]
