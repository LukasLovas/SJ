import os
import sys

from analyzer import Analyzer
from grammar import Grammar


class Main:
    def __init__(self):
        self.grammar = Grammar()
        self.analyzer = Analyzer(self.grammar)

    def run(self, arguments):
        if len(arguments) == 1:
            return self.run_interactive()

        if len(arguments) not in (3, 4):
            self.print_usage()
            return 2

        input_file = arguments[1]
        output_file = arguments[2]
        recovery = "off"

        if len(arguments) == 4:
            recovery = arguments[3].strip().lower()
            if recovery not in ("off", "panic"):
                print("Neplatny recovery mode: " + arguments[3])
                self.print_usage()
                return 2

        if not self.load_default_table():
            return 1
        return self.run_analysis(input_file, output_file, recovery)

    def run_interactive(self):
        if not self.load_default_table():
            return 1

        inputs_directory = self.project_path("inputs")
        outputs_directory = self.project_path("outputs")

        input_files = self.list_input_files(inputs_directory)

        print("littleXML LL(1) analyzator")
        print("")
        print("Dostupne vstupy:")
        if len(input_files) == 0:
            print("  (v priecinku inputs nie su ziadne vstupne subory)")
        else:
            for index, file_name in enumerate(input_files, start=1):
                print("  " + str(index) + ". " + file_name)

        custom_choice = len(input_files) + 1
        print("  " + str(custom_choice) + ". Vlastny vstup")

        selected_index = self.read_choice("Vyber vstupny subor", custom_choice)
        if selected_index is None:
            return 2

        if selected_index == len(input_files):
            input_path = self.read_custom_input_path()
            if input_path is None:
                return 2
            input_file = input_path
        else:
            input_file = input_files[selected_index]
            input_path = os.path.join(inputs_directory, input_file)

        recovery = self.read_recovery_mode()
        if recovery is None:
            return 2

        output_file = self.output_file_name(input_file, recovery)
        output_path = os.path.join(outputs_directory, output_file)

        try:
            os.makedirs(outputs_directory, exist_ok=True)
        except OSError as error:
            print("Vystupny priecinok sa nepodarilo vytvorit: " + str(error))
            return 1

        return self.run_analysis(input_path, output_path, recovery)

    def run_analysis(self, input_file, output_file, recovery):
        try:
            with open(input_file, "r", encoding="utf-8") as source_file:
                source = source_file.read()
        except OSError as error:
            print("Vstupny subor sa nepodarilo nacitat: " + str(error))
            return 1

        result = self.analyzer.analyze(source, recovery)
        report = result.format_report(source, input_file, recovery)

        if not self.ensure_output_directory(output_file):
            return 1

        try:
            with open(output_file, "w", encoding="utf-8") as report_file:
                report_file.write(report)
                report_file.write("\n")
        except OSError as error:
            print("Vystupny subor sa nepodarilo zapisat: " + str(error))
            return 1

        print(report)
        print("")
        print("Report zapisany do: " + output_file)

        if result.accepted:
            return 0
        return 1

    def ensure_output_directory(self, output_file):
        directory = os.path.dirname(os.path.abspath(output_file))
        if directory == "":
            return True

        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as error:
            print("Vystupny priecinok sa nepodarilo vytvorit: " + str(error))
            return False

        return True

    def list_input_files(self, inputs_directory):
        try:
            names = os.listdir(inputs_directory)
        except OSError:
            return []

        files = []
        for name in names:
            path = os.path.join(inputs_directory, name)
            if os.path.isfile(path):
                files.append(name)
        files.sort()
        return files

    def read_custom_input_path(self):
        print("Priklad cesty: .\\projekt\\inputs\\01_valid_empty_element.xml")
        raw_value = input("Zadaj cestu k vstupnemu suboru: ").strip()
        if raw_value == "":
            print("Cesta k vstupnemu suboru nemoze byt prazdna.")
            return None

        return os.path.expanduser(raw_value.strip("\"'"))

    def read_choice(self, label, count):
        raw_value = input(label + " [1-" + str(count) + "]: ").strip()
        try:
            value = int(raw_value)
        except ValueError:
            print("Neplatna volba: " + raw_value)
            return None

        if value < 1 or value > count:
            print("Volba musi byt od 1 do " + str(count) + ".")
            return None

        return value - 1

    def read_recovery_mode(self):
        print("")
        print("Recovery mode:")
        print("  1. off")
        print("  2. panic")
        raw_value = input("Vyber recovery mode [1-2, Enter=off]: ").strip().lower()

        if raw_value == "" or raw_value == "1" or raw_value == "off":
            return "off"
        if raw_value == "2" or raw_value == "panic":
            return "panic"

        print("Neplatny recovery mode: " + raw_value)
        return None

    def output_file_name(self, input_file, recovery):
        base_name = os.path.basename(input_file)
        name_without_extension, _extension = os.path.splitext(base_name)
        return name_without_extension + "_" + recovery + "_report.txt"

    def print_usage(self):
        print("Pouzitie:")
        print("  python .\\projekt\\main.py")
        print("  python .\\projekt\\main.py <vstupny_subor> <vystupny_subor> [off|panic]")
        print("")
        print("Priklady:")
        print("  python .\\projekt\\main.py")
        print("  python .\\projekt\\main.py .\\projekt\\inputs\\01_valid_empty_element.xml .\\projekt\\outputs\\manual_report.txt")
        print("  python .\\projekt\\main.py .\\projekt\\inputs\\07_invalid_two_nested_children.xml .\\projekt\\outputs\\panic_report.txt panic")

    def load_default_table(self):
        table_file = self.default_table_path()
        try:
            self.grammar.load_table(table_file)
        except Exception as error:
            print("Prechodovu tabulku sa nepodarilo nacitat: " + str(error))
            print("Ocakavany subor: " + table_file)
            return False
        return True

    def default_table_path(self):
        normalized = __file__.replace("\\", "/")
        if "/" not in normalized:
            return "table.csv"
        directory = normalized.rsplit("/", 1)[0]
        return directory + "/table.csv"

    def project_path(self, child):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), child)


if __name__ == "__main__":
    sys.exit(Main().run(sys.argv))
