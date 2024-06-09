import pytest
import sys

from pathlib import Path
from reporter_cli import cli, model


@pytest.fixture
def mock_text_processor(monkeypatch):
    class MockTextProcessor:
        def __init__(self):
            self.project_name = "ProjectName"

        def extract_tables(self):
            return ['table1', 'table2']

    monkeypatch.setattr(model, 'TextProcessor', MockTextProcessor)


@pytest.fixture
def mock_path_exists(monkeypatch):
    def mock_exists(path):
        return True

    monkeypatch.setattr(Path, "exists", mock_exists)


@pytest.fixture
def mock_renderer(monkeypatch):
    class MockBOMRenderer:
        def __init__(self, bom, template_file=None):
            if template_file:
                with open(template_file, 'r') as f:
                    self.template_content = f.read()
            self.output = "Rendered Output"

        def write_file(self, output_file):
            pass

    monkeypatch.setattr(model, 'BOMRenderer', MockBOMRenderer)


def test_parse_args():
    test_args = ["cli.py", "--input", "input.txt", "--output", "output.txt", "--template", "template.txt"]
    sys.argv = test_args
    args = cli.parse_args()
    assert args.input == "input.txt"
    assert args.output == "output.txt"
    assert args.template == "template.txt"


def test_main_output_file_exists(mock_path_exists, monkeypatch, tmp_path):
    monkeypatch.setattr('builtins.input', lambda _: 'no')

    # Create temporary input and output files
    input_file = tmp_path / "input.txt"
    input_file.write_text("dummy data")

    output_file = tmp_path / "output.txt"
    output_file.write_text("existing output data")

    template_file = tmp_path / "template.txt"
    template_file.write_text("template data")

    test_args = ["cli.py", "--input", str(input_file), "--output", str(output_file)]
    sys.argv = test_args
    args = cli.parse_args()
    with pytest.raises(SystemExit) as exc_info:
        cli.main(args)
    assert exc_info.value.code == 0


def test_main_input_file_not_exists(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "exists", lambda path: False)

    test_args = ["cli.py", "--input", str(tmp_path / "input.txt")]
    sys.argv = test_args
    args = cli.parse_args()
    with pytest.raises(SystemExit) as exc_info:
        cli.main(args)
    assert exc_info.value.code == 1


def test_main_template_file_not_exists(monkeypatch, tmp_path):
    def mock_exists(path):
        if "input.txt" in str(path):
            return True
        if "reporter_cli/templates/template.txt" in str(path):
            return False
        return False
    monkeypatch.setattr(Path, "exists", mock_exists)

    # Create a temporary input file
    input_file = tmp_path / "input.txt"
    input_file.write_text("dummy data")

    test_args = ["cli.py", "--input", str(input_file), "--template", "test"]
    sys.argv = test_args
    args = cli.parse_args()
    with pytest.raises(SystemExit) as exc_info:
        cli.main(args)
    assert exc_info.value.code == 1


def test_main(mock_text_processor, mock_path_exists, mock_renderer, monkeypatch, tmp_path):
    monkeypatch.setattr('builtins.input', lambda _: 'yes')

    # Create temporary input and template files
    input_file = tmp_path / "input.txt"
    input_file.write_text('''
    | Tables |  LPrice |
    |--------|--------|
    |    A   |  $1600 |
    |    B   |    $12 |
    |    C   |     $1 |''')

    template_file = tmp_path / "template.txt"
    template_file.write_text("template data")

    output_file = tmp_path / "output.txt"

    test_args = ["cli.py", "--input", str(input_file), "--output", str(output_file), "--template", 'test']
    sys.argv = test_args
    args = cli.parse_args()
    cli.main(args)

    assert True  # If no exception, the test passes


def test_successful_rendering_without_overwriting(mock_text_processor, mock_path_exists, mock_renderer, monkeypatch,
                                                  tmp_path):
    # Mock the input function to simulate user confirmation
    monkeypatch.setattr('builtins.input', lambda _: 'yes')

    # Create temporary input and template files
    input_file = tmp_path / "input.txt"
    input_file.write_text('''
| Tables |  LPrice |
|--------|--------|
|    A   |  $1600 |
|    B   |    $12 |
|    C   |     $1 |''')

    template_file = tmp_path / "template.txt"
    template_file.write_text("template data")

    output_file = tmp_path / "output.txt"

    # Ensure the output file exists to test overwriting
    output_file.write_text("existing output data")

    test_args = ["cli.py", "--input", str(input_file), "--output", str(output_file), "--template", "test"]
    sys.argv = test_args
    args = cli.parse_args()
    cli.main(args)

    # Check if the output file was written correctly
    with open(output_file, 'r') as f:
        content = f.read()
    assert content == "test-template"


def test_invalid_input_file(mock_text_processor, mock_path_exists, mock_renderer, monkeypatch, tmp_path):
    monkeypatch.setattr('builtins.input', lambda _: 'yes')
    # Create a temporary input file that is invalid (e.g., directory instead of file)
    input_file = tmp_path / "invalid_input"
    input_file.mkdir()

    test_args = ["cli.py", "--input", str(input_file), "--output", str(tmp_path / "output.txt")]
    sys.argv = test_args
    args = cli.parse_args()
    with pytest.raises(SystemExit) as exc_info:
        cli.main(args)
    assert exc_info.value.code == 1

def test_input_file_with_no_tables(mock_text_processor, mock_path_exists, mock_renderer, monkeypatch, tmp_path):
    monkeypatch.setattr('builtins.input', lambda _: 'yes')
    # Create a temporary input file that is invalid (e.g., directory instead of file)
    input_file = tmp_path / "input.txt"
    input_file.write_text('''Look no tables''')

    test_args = ["cli.py", "--input", str(input_file), "--output", str(tmp_path / "output.txt")]
    sys.argv = test_args
    args = cli.parse_args()
    with pytest.raises(SystemExit) as exc_info:
        cli.main(args)
    assert exc_info.value.code == 0


def test_error_during_processing(monkeypatch, tmp_path):
    # Mock class to replace TextProcessor
    class MockTextProcessor:
        def __init__(self, *args, **kwargs):
            print("MockTextProcessor initialized")
            self.project_name = "ProjectName"

        def extract_tables(self):
            print("MockTextProcessor extract_tables called")
            raise Exception("Processing error")

    # Use monkeypatch to replace TextProcessor with MockTextProcessorUnique
    monkeypatch.setattr('reporter_cli.cli.TextProcessor', MockTextProcessor)

    # Create a temporary input file
    input_file = tmp_path / "input.txt"
    input_file.write_text('''
    | Tables |  LPrice |
    |--------|--------|
    |    A   |  $1600 |
    |    B   |    $12 |
    |    C   |     $1 |''')

    # Set up test arguments
    test_args = ["cli.py", "--input", str(input_file), "--output", str(tmp_path / "output.txt")]
    sys.argv = test_args
    args = cli.parse_args()

    # Print statements to trace the test flow
    print("Running test_error_during_processing")

    # Ensure SystemExit is raised due to processing error
    with pytest.raises(SystemExit) as exc_info:
        cli.main(args)
    print(f"Exited with code: {exc_info.value.code}")
    assert exc_info.value.code == 1


def test_error_during_bom(monkeypatch, tmp_path):
    # Mock class to replace TextProcessor
    class MockTableBOM:
        def __init__(self, *args, **kwargs):
            print("MockTableBOM initialized")
            self.tables = [['a', 'b'], [['a'], ['b']]]
            self.total_cost = 0.0
            self.project_name = 'Test'
            self.bill_of_materials = self.make_bom()

        def make_bom(self):
            print("MockTableBOM make_bom called")
            raise Exception("table conversion error")

    # Use monkeypatch to replace TextProcessor with MockTextProcessorUnique
    monkeypatch.setattr('reporter_cli.cli.TableBOM', MockTableBOM)

    # Create a temporary input file
    input_file = tmp_path / "input.txt"
    input_file.write_text('''
    | Tables |  LPrice |
    |--------|--------|
    |    A   |  $1600 |
    |    B   |    $12 |
    |    C   |     $1 |''')

    # Set up test arguments
    test_args = ["cli.py", "--input", str(input_file), "--output", str(tmp_path / "output.txt")]
    sys.argv = test_args
    args = cli.parse_args()

    # Print statements to trace the test flow
    print("Running test_error_during_bom")

    # Ensure SystemExit is raised due to processing error
    with pytest.raises(SystemExit) as exc_info:
        cli.main(args)
    print(f"Exited with code: {exc_info.value.code}")
    assert exc_info.value.code == 1
