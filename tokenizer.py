import re

from grammar import Grammar
from token import ErrorLog, Token


class Tokenizer:
    WHITESPACE = re.compile(r"\s+")
    TOKEN_PATTERNS = (
        ("<?xml", re.compile(r"<\?xml")),
        ("version=", re.compile(r"version=")),
        ("?>", re.compile(r"\?>")),
        ("</", re.compile(r"</")),
        ("/>", re.compile(r"/>")),
        ("<", re.compile(r"<")),
        (">", re.compile(r">")),
        (".", re.compile(r"\.")),
        ("-", re.compile(r"-")),
        (":", re.compile(r":")),
        ("_", re.compile(r"_")),
        ("!", re.compile(r"!")),
        ("@", re.compile(r"@")),
        ("#", re.compile(r"#")),
        ("LETTER", re.compile(r"[A-Za-z]")),
        ("NUMBER", re.compile(r"[0-9]")),
    )

    def __init__(self, source, recovery):
        self.source = source
        self.recovery = recovery
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        self.diagnostics = []

    def tokenize(self):
        while self.position < len(self.source):
            whitespace = self.WHITESPACE.match(self.source, self.position)
            if whitespace is not None:
                self.advance_position(whitespace.group(0))
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

        self.tokens.append(Token(Grammar.EOF, Grammar.EOF, self.line, self.column, self.position))
        return self.tokens

    def next_token(self):
        match = self.best_token_match()
        if match is None:
            return None

        token_type, value = match
        return self.build_token_and_advance(token_type, value)

    def best_token_match(self):
        best_type = None
        best_value = None

        for token_type, pattern in self.TOKEN_PATTERNS:
            match = pattern.match(self.source, self.position)
            if match is None:
                continue

            value = match.group(0)
            if best_value is None or len(value) > len(best_value):
                best_type = token_type
                best_value = value

        if best_type is None:
            return None
        return best_type, best_value

    def starts_token(self):
        return self.best_token_match() is not None

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
            if self.WHITESPACE.match(self.source, self.position) is not None:
                break
            if self.starts_token():
                break
            self.advance_position(self.source[self.position])

        if self.position == start:
            self.advance_position(self.source[self.position])

        return self.source[start:self.position]
