import pytest
from pathlib import Path
from reporter_cli.model import TextProcessor, TableBOM, BOMRenderer
from jinja2 import Template
import tempfile


@pytest.fixture
def sample_text():
    return """
# Project Name

| Header1 | Header2 |
|---------|---------|
| Data1   | $10.00  |
| Data2   | $20.00  |

| Another Header1 | Another Header2 |
|----------------|------------------|
| Another Data1  | $30.00           |
| Another Data2  | $40.00           |
"""


@pytest.fixture
def mock_template_dir(tmp_path):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_file = template_dir / "project_summary_template"
    template_file.write_text("Project: {{ title }}\nTotal Cost: {{ total_cost }}")
    return str(template_dir)


def test_text_processor_initialization(tmp_path, sample_text):
    # Create a temporary file with sample text
    input_file = tmp_path / "input.txt"
    input_file.write_text(sample_text)

    # Initialize TextProcessor
    processor = TextProcessor(str(input_file))

    # Check if the file was read correctly
    assert processor.text == sample_text
    assert processor.project_name == "Project Name"


def test_text_processor_extract_tables(tmp_path, sample_text):
    # Create a temporary file with sample text
    input_file = tmp_path / "input.txt"
    input_file.write_text(sample_text)

    # Initialize TextProcessor
    processor = TextProcessor(str(input_file))

    # Extract tables
    tables = processor.extract_tables()

    # Check if tables are extracted correctly
    assert len(tables) == 2
    assert tables[0][0] == ["Header1", "Header2"]
    assert tables[0][1] == [["Data1", "$10.00"], ["Data2", "$20.00"]]
    assert tables[1][0] == ["Another Header1", "Another Header2"]
    assert tables[1][1] == [["Another Data1", "$30.00"], ["Another Data2", "$40.00"]]


def test_table_bom_initialization():
    tables = [
        (["Header1", "Header2"], [["Data1", "$10.00"], ["Data2", "$20.00"]]),
        (["Another Header1", "Another Header2"], [["Another Data1", "$30.00"], ["Another Data2", "$40.00"]]),
        (["Header1", "Price"], [["Data1", "$10.00"], ["Data2", "$20.00"]]),

    ]
    project_name = "Project Name"

    # Initialize TableBOM
    bom = TableBOM(tables, project_name)

    # Check if BOM was created correctly
    assert bom.project_name == project_name
    assert bom.total_cost == 130.00
    assert "Header1" in bom.bill_of_materials
    assert "Another Header1" in bom.bill_of_materials


def test_bom_renderer_initialization(tmp_path, mock_template_dir):
    tables = [
        (["Header1", "Header2"], [["Data1", "$10.00"], ["Data2", "$20.00"]]),
    ]
    project_name = "Project Name"

    # Initialize TableBOM
    bom = TableBOM(tables, project_name)

    # Initialize BOMRenderer
    renderer = BOMRenderer(bom, template="project_summary_template")

    # Check if the output was rendered correctly
    expected_output = '''Project `Project Name` requires the following material:

Header1:

Data1 - ($10.00).
Data2 - ($20.00).

Subtotal for Header1: $30.00


The total cost will be $30.00.'''
    print(renderer.output)
    assert renderer.output == expected_output


def test_bom_renderer_write_file(tmp_path, mock_template_dir):
    tables = [
        (["Header1", "Header2"], [["Data1", "$10.00"], ["Data2", "$20.00"]]),
    ]
    project_name = "Project Name"

    # Initialize TableBOM
    bom = TableBOM(tables, project_name)

    # Initialize BOMRenderer
    renderer = BOMRenderer(bom, template="project_summary_template")

    # Write the output to a file
    output_file = tmp_path / "output.txt"
    renderer.write_file(output_file)

    # Check if the file was written correctly
    with open(output_file, 'r') as f:
        content = f.read()
        #print(content)
        expected_output = '''Project `Project Name` requires the following material:

Header1:

Data1 - ($10.00).
Data2 - ($20.00).

Subtotal for Header1: $30.00


The total cost will be $30.00.'''
    assert content == expected_output
