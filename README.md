# Reporter CLI

## Setup Instructions

### Using Docker

1. Build the Docker image:
    ```bash
    docker build -t reporter-cli .
    ```

2. Run the Docker container:
    ```bash
    docker run --rm reporter-cli
    ```

### Local Installation

#### Requires Python 3.11+

1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/your-repo-name.git
    cd your-repo-name
    ```

2. **Create and activate a virtual environment**:

4. **Install the package with:**
    ```bash
    pip install -e .
    ```

5. **Run the CLI tool**:
    ```bash
    reporter --input example_input.txt
    ```

## Running Tests

**Run tests with pytest**
```bash
pytest
```

## Usage

The `reporter` CLI tool processes an input file and outputs the result to a specified file using a template (which can be specified).

### Commands and Options

- `--input <file>`: (Required) Specifies the input file to process.
- `--output <file>`: (Optional) Specifies the output file. If not provided, the output will be written to a file named `<input_file_stem>_output.<input_file_extension>`.
- `--template <file>`: (Optional) Specifies the template file to use for rendering the output. If not provided, a default template will be used.

### Examples

1. **Basic Example**:
   Process an input file and output the result to a default output file.
   ```bash
   reporter --input example_input.txt
   ```
2. **Specific Template**:
   Process an input file and output the result using the more boring template, rather than the one that groups the materials by material type.
   ```bash
   reporter --input example_input.txt --template boring
   ```
3. **Specific Output Location**:
   Process an input file and output the result using a customer output path and filename but with the fancy default template :) 
   ```bash
   reporter --input example_input.txt --output example_output.txt
    ```