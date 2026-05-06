from grammar import Grammar
from token import ErrorLog


class Parser:
    def __init__(self, tokens, grammar, recovery):
        self.tokens = tokens
        self.grammar = grammar
        self.recovery = recovery
        self.index = 0
        self.stack = [Grammar.EOF, Grammar.START_SYMBOL]
        self.diagnostics = []
        self.log = []
        self.rule_sequence = []
        self.accepted = False

    def parse(self):
        step = 1
        while len(self.stack) > 0:
            top = self.stack.pop()
            lookahead = self.current_token()
            input_index_before = self.index
            stack_before = self.stack[:] + [top]

            if top == Grammar.EPSILON:
                action = "epsilon"
            elif self.grammar.is_terminal(top):
                action = self.match_terminal(top, lookahead)
            elif self.grammar.is_non_terminal(top):
                action = self.expand_non_terminal(top, lookahead)
            else:
                action = "internal error: unknown symbol " + top
                self.diagnostics.append(ErrorLog("SA", action, lookahead))

            self.add_log(step, stack_before, lookahead, action, input_index_before)
            step += 1

            if self.recovery == "off" and len(self.diagnostics) > 0:
                break

        self.accepted = (
            len(self.diagnostics) == 0
            and self.current_token().token_type == Grammar.EOF
            and len(self.stack) == 0
        )

        if not self.accepted and len(self.diagnostics) == 0:
            self.diagnostics.append(
                ErrorLog("SA", "input was not fully consumed", self.current_token())
            )

        return self.accepted

    def current_token(self):
        if self.index >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.index]

    def match_terminal(self, expected, lookahead):
        if expected == lookahead.token_type:
            self.index += 1
            return "match " + expected

        message = "expected " + expected + ", got " + lookahead.token_type
        self.diagnostics.append(ErrorLog("SA", message, lookahead))

        if self.recovery == "panic":
            if lookahead.token_type != Grammar.EOF:
                self.index += 1
                return "panic: discard unexpected " + lookahead.token_type + "; " + message
            return "panic: cannot discard $; " + message

        return "error: " + message

    def expand_non_terminal(self, non_terminal, lookahead):
        row = self.grammar.table.get(non_terminal, {})
        rule_id = row.get(lookahead.token_type)

        if rule_id is not None:
            left_side, production = self.grammar.rule(rule_id)
            if left_side != non_terminal:
                message = (
                    "table selected rule "
                    + str(rule_id)
                    + " for "
                    + non_terminal
                    + ", but rule left side is "
                    + left_side
                )
                self.diagnostics.append(ErrorLog("SA", message, lookahead))
                return "internal error: " + message

            for symbol in reversed(production):
                self.stack.append(symbol)
            self.rule_sequence.append(rule_id)
            if len(production) == 0:
                right_side = Grammar.EPSILON
            else:
                right_side = " ".join(production)
            return "rule " + str(rule_id) + ": " + non_terminal + " -> " + right_side

        expected = []
        for terminal in row:
            expected.append(terminal)
        expected.sort()

        message = (
            "no rule for "
            + non_terminal
            + " with lookahead "
            + lookahead.token_type
            + "; expected one of "
            + ", ".join(expected)
        )
        self.diagnostics.append(ErrorLog("SA", message, lookahead))

        if self.recovery == "panic":
            sync = Grammar.FOLLOW.get(non_terminal, (Grammar.EOF,))
            if lookahead.token_type in sync:
                return "panic: synchronize by popping " + non_terminal

            skipped = []
            while self.current_token().token_type not in sync and self.current_token().token_type != Grammar.EOF:
                skipped.append(self.current_token().token_type)
                self.index += 1

            if len(skipped) == 0:
                skipped_text = "nothing"
            else:
                skipped_text = ", ".join(skipped)

            return (
                "panic: skipped "
                + skipped_text
                + "; sync("
                + non_terminal
                + ")={"
                + ", ".join(sync)
                + "}"
            )

        return "error: " + message

    def add_log(self, step, stack_before, lookahead, action, input_index_before):
        input_before = []
        for token in self.tokens[input_index_before:]:
            input_before.append(token.short())

        input_after = []
        for token in self.tokens[self.index:]:
            input_after.append(token.short())

        stack_before_items = []
        for symbol in reversed(stack_before):
            stack_before_items.append(symbol)

        stack_after_items = []
        for symbol in reversed(self.stack):
            stack_after_items.append(symbol)

        self.log.append(
            self.format_iteration(
                step,
                stack_before_items,
                lookahead,
                input_before,
                action,
                stack_after_items,
                input_after,
            )
        )

    def format_iteration(
        self,
        step,
        stack_before,
        lookahead,
        input_before,
        action,
        stack_after,
        input_after,
    ):
        width = 92
        separator = "-" * width
        lines = [
            separator,
            "Iteracia " + str(step).rjust(3, "0"),
            self.format_log_row("Zasobnik pred", self.join_or_empty(stack_before), width),
            self.format_log_row("Vstup pred", self.join_or_empty(input_before), width),
            self.format_log_row(
                "Peek",
                lookahead.short() + " (riadok " + str(lookahead.line) + ", stlpec " + str(lookahead.column) + ")",
                width,
            ),
            self.format_log_row("Krok", action, width),
            self.format_log_row("Zasobnik po", self.join_or_empty(stack_after), width),
            self.format_log_row("Vstup po", self.join_or_empty(input_after), width),
        ]
        return "\n".join(lines)

    def format_log_row(self, label, value, width):
        prefix = label.ljust(14) + ": "
        available = width - len(prefix)
        lines = []
        chunks = self.wrap_value(value, available)
        continuation = "".ljust(14) + "  "
        for index, chunk in enumerate(chunks):
            if index == 0:
                lines.append(prefix + chunk)
            else:
                lines.append(continuation + chunk)
        return "\n".join(lines)

    def join_or_empty(self, items):
        if len(items) == 0:
            return "(prazdne)"
        return " ".join(items)

    def wrap_value(self, value, width):
        if len(value) <= width:
            return [value]

        chunks = []
        current = ""
        for word in value.split(" "):
            if current == "":
                current = word
            elif len(current) + 1 + len(word) <= width:
                current += " " + word
            else:
                chunks.append(current)
                current = word

            while len(current) > width:
                chunks.append(current[:width])
                current = current[width:]

        if current != "":
            chunks.append(current)
        return chunks
