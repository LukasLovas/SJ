class Token:
    def __init__(self, token_type, value, line, column, index):
        self.token_type = token_type
        self.value = value
        self.line = line
        self.column = column
        self.index = index

    def short(self):
        if self.token_type == "$":
            return "$"

        if self.token_type == "LETTER" or self.token_type == "NUMBER":
            return self.token_type + "(" + repr(self.value) + ")"

        if self.value and self.value != self.token_type:
            return self.token_type + "(" + repr(self.value) + ")"
        return self.token_type

    def __str__(self):
        return str(self.line) + ":" + str(self.column) + " " + self.short()


class ErrorLog:
    def __init__(self, phase, message, token=None):
        self.phase = phase
        self.message = message
        self.token = token

    def __str__(self):
        if self.token is None:
            return self.phase + ": " + self.message
        return (
            self.phase
            + " at "
            + str(self.token.line)
            + ":"
            + str(self.token.column)
            + ": "
            + self.message
            + " ["
            + self.token.short()
            + "]"
        )
