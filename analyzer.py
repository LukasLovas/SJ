from parser import Parser
from tokenizer import Tokenizer


class Analyzer:
    def __init__(self, grammar):
        self.grammar = grammar

    def analyze(self, source, recovery):
        tokenizer = Tokenizer(source, recovery)
        tokens = tokenizer.tokenize()

        parser = Parser(tokens, self.grammar, recovery)
        parser.parse()

        diagnostics = []
        diagnostics.extend(tokenizer.diagnostics)
        diagnostics.extend(parser.diagnostics)

        accepted = len(diagnostics) == 0 and parser.accepted
        return AnalysisResult(
            accepted,
            tokens,
            parser.log,
            diagnostics,
            parser.rule_sequence,
            self.grammar.format_transition_table(),
        )


class AnalysisResult:
    def __init__(self, accepted, tokens, log, diagnostics, rule_sequence, transition_table):
        self.accepted = accepted
        self.tokens = tokens
        self.log = log
        self.diagnostics = diagnostics
        self.rule_sequence = rule_sequence
        self.transition_table = transition_table

    def format_report(self, source, input_file, recovery):
        lines = []
        lines.append("=" * 92)
        lines.append("littleXML LL(1) analyza")
        lines.append("=" * 92)
        lines.append("Vstupny subor : " + input_file)
        lines.append("Recovery mode : " + recovery)
        lines.append("")
        lines.append("Vstup:")
        lines.append(source)
        lines.append("")
        lines.append("-" * 92)
        lines.append("Pravidla gramatiky")
        lines.append("-" * 92)
        for line in self.transition_table:
            lines.append(line)

        lines.append("")
        lines.append("-" * 92)
        lines.append("Tokeny")
        lines.append("-" * 92)
        for index, token in enumerate(self.tokens, start=1):
            lines.append(str(index).rjust(3, "0") + " | " + str(token))

        lines.append("")
        lines.append("-" * 92)
        lines.append("Log syntaktickeho analyzatora")
        lines.append("-" * 92)
        for line in self.log:
            lines.append(line)

        lines.append("")
        lines.append("-" * 92)
        lines.append("Pouzite pravidla")
        lines.append("-" * 92)
        if len(self.rule_sequence) == 0:
            lines.append("(ziadne)")
        else:
            lines.append(", ".join(str(rule_id) for rule_id in self.rule_sequence))

        lines.append("")
        lines.append("-" * 92)
        lines.append("Problemy validacie")
        lines.append("-" * 92)
        if len(self.diagnostics) == 0:
            lines.append("(ziadne)")
        else:
            for diagnostic in self.diagnostics:
                lines.append(str(diagnostic))

        lines.append("")
        lines.append("=" * 92)
        if self.accepted:
            lines.append("VYSLEDOK: SYNTAX OK")
        else:
            lines.append("VYSLEDOK: SYNTAX ERROR")
        lines.append("=" * 92)
        return "\n".join(lines)
