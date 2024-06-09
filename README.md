# Reporter CLI

This is a tool that can extract tables (in Markdown format) from a textfile like this:

```text
# A fancy title

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.


| Tables |  Price |
|--------|--------|
|    A   |  $1600 |
|    B   |    $12 |
|    C   |     $1 |


Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt
mollit anim id.


| Chairs |  Price |
|--------|--------|
|   AA   |    $10 |
|    Z   |     $1 |
|   FOO  |     $1 |

```

This tool will assume that the first # line is the project name, and will then compile the tables, under the assumption that the first column tells us a material, and that there is at least one column containing prices, by virtue of having numbers with a currency prefix. It only keeps the first column that has currency.
This is then composed into a bill of materials and will output something like this:

```text
Project `A fancy title` requires the following material:

Chairs:

 AA - ($10.00).
  Z - ($1.00).
FOO - ($1.00).

Subtotal for Chairs: $12.00

Tables:

  A - ($1600.00).
  B - ($12.00).
  C - ($1.00).

Subtotal for Tables: $1613.00


The total cost will be $1625.00.
```


## Setup Instructions

### Using Docker

1. Build the Docker image from included Dockerfile, which builds and tests the package:
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
    git clone https://github.com/foskaos/reporter.git
    cd reporter
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

The `reporter` CLI tool processes an input file and outputs the result to a specified file using a template (which can be specified) or to the console.

### Commands and Options

- `--input <file>`: (Required) Specifies the input file to process.
- `--output <file>`: (Optional) Specifies the output file. If not provided, the output will be written to a file named `<input_file_stem>_output.<input_file_extension>`.
- `--template <file>`: (Optional) Specifies the template file to use for rendering the output. If not provided, a default template will be used.
- `--console`: (Optional) Prints template to the console.

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
   Process an input file and output the result using a custome output path and filename but with the fancy default template :) 
   ```bash
   reporter --input example_input.txt --output example_output.txt
    ```
4. **Print template to the console**:
   Put the contents of the template on the console with the --console option
   ```bash
   reporter --input example_input.txt --console
    ```

## Improvements to Consider

I've followed the brief pretty closely, I've made some assumptions (e.g. any number of columns, header item 0 is the material type (eg. tables)) but here are some improvements that would be fun to discuss:

1. **Better Column Type Detection**:
   Currently (naively) looks for a column that could be currency and uses that to create a BOM.
   1. Take arguments specifying what the columns contain.
   2. Could total/subtotal any numerical column and distinguish from currency columns. Currently depends on currency being {{Symbol}}{{Value}}
2. **Advanced Analysis**
   We are handling any number of columns and assuming the first item in the header row is effectively the object type, and that there must be at least one rigidly detected currency column if not it doesn't make a BOM. Could detect columns with multiple currencies and get live exchange rates and provide a normalized total and subtotal in a selected currency, or use column names as hints
3. **LLM Table extraction**
   Could put an LLM in the pipeline to recognize tables and return json with function calling, especially useful if tables are a bit less narrowly defined, or using mixed delimiters. As is, this tool could be useful in labelling a training data set.
4. **Unix Pipes**
   Could be used with unix pipes: e.g. cat input.txt | reporter
5. **Multiple files/Directory handling**
   Could be cool to handle directories instead of individual files. Or pass a list of files.
6. **Semi-Structed output**
   In the context of a wider project, it might make more sense to output json or csv for use in database, DataFrames etc.
7. **More Templates**
