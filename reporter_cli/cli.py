import argparse
import sys

from pathlib import Path
from reporter_cli.model import TextProcessor, TableBOM, BOMRenderer


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, required=True, help='Input file name')
    parser.add_argument('--output', type=str, required=False, help='Output file name')
    parser.add_argument('--template', type=str, required=False, help='Template name')
    parser.add_argument('--console', action='store_true', required=False, help='Prints template to console')
    return parser.parse_args()


def main(args):
    input_file = Path(args.input)
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = input_file.with_name(f"{input_file.stem}_output{input_file.suffix}")

    template_file = f"{args.template}" if args.template else None

    if template_file:
        tf = Path(template_file)
        templ_dir = tf.parents[0]

    # Check if input file exists
    if not input_file.exists():
        print(f"Error: Input file '{input_file}' does not exist.")
        sys.exit(1)

    # Check if template file exists in templates/ folder, if provided
    if template_file and not Path(f"reporter_cli/templates/{template_file}").exists():
        print(f"Error: Template file '{template_file}' does not exist.")
        sys.exit(1)

    # Warn if output file exists
    if output_file.exists():
        overwrite = input(f"Warning: Output file '{output_file}' already exists, are you ok with this overwriting? (yes/no): ")
        if not (overwrite.lower() == 'yes' or overwrite.lower() == 'y'):
            print("Operation aborted by the user.")
            sys.exit(0)

    # Process input file and extract any tables + project name from first line starting with #
    try:
        processor = TextProcessor(input_file)
        tables = processor.tables
        project_name = processor.project_name
    except Exception as e:
        print(f"Error processing input file: {e}")
        sys.exit(1)

    if not tables:
        print('No tables extracted, exiting')
        sys.exit(0)

    # Create a bill of materials that can be nicely rendered
    try:
        bill_of_materials = TableBOM(tables, project_name)
    except Exception as e:
        print(f"Error converting table to bill of materials: {e}")
        sys.exit(1)



    # try to render the file as a string
    try:
        if template_file:
            renderer = BOMRenderer(bill_of_materials, template_file)
        else:
            renderer = BOMRenderer(bill_of_materials)
    except Exception as e:
        print(f"Error during rendering: {e}")
        sys.exit(1)

    if args.console:
        print(renderer.output)

    # Write the output file
    try:
        renderer.write_file(output_file)
    except Exception as e:
        print(f"Error writting file: {e}")
        sys.exit(1)


def cli():
    args = parse_args()
    main(args)

if __name__ == "__main__":
    cli()