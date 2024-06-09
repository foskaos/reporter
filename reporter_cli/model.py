from pathlib import Path
import re
from typing import Tuple, List, Dict, Optional
from jinja2 import Environment, select_autoescape, PackageLoader


class TextProcessor:
    """ Class to encapuslate opening a file and extracting tables and project name """
    def __init__(self,
                 filename: Path):
        self.filename = Path(filename)
        self.text = self._read_file()
        self.project_name = None
        self.tables = self.extract_tables()

    def _read_file(self):
        with self.filename.open('r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def _process_table(table: List) -> Tuple[List, List]:
        """ Extract header and rows from table """
        try:
            header = [cell.strip() for cell in table[0].split('|') if cell.strip()]
        except Exception as e:
            print(f'Header Could not be Parsed. Error:{e}')
            header = []
        try:
            data = []
            for row in table[2:]:
                cells = [cell.strip() for cell in row.split('|') if cell.strip()]
                if len(cells) == len(header):
                    data.append(cells)
        except Exception as e:
            print(f'Data Could not be Parsed. Error:{e}')
            data = []
        return header, data

    def extract_tables(self) -> List:
        """ Extract Tables from text"""
        tables = []
        current_table = []
        inside_table = False
        try:
            for line in self.text.splitlines():
                line = line.strip()
                if line.startswith('|') and line.endswith('|'):
                    if not inside_table:
                        inside_table = True
                        current_table = [line]
                    else:
                        current_table.append(line)
                elif line.startswith('#'):
                    if not self.project_name:
                        self.project_name = ''.join(line[1:].strip())
                else:
                    if inside_table:
                        inside_table = False
                        if len(current_table) >= 2:
                            tables.append(self._process_table(current_table))
                        current_table = []

            if inside_table and len(current_table) >= 2:
                tables.append(self._process_table(current_table))
        except Exception as e:
            print(f'Could not extract tables from provided text. Error: {e}')
        return tables


class TableBOM:
    """ Class to interpret and extracted table as a bill of materials """
    def __init__(self,
                 tables: list,
                 project_name: str):
        self.tables = tables
        self.total_cost = 0.0
        self.currency_symbol = None
        self.bill_of_materials = self.make_bom()
        self.project_name = project_name

    def __repr__(self):
        return f"{self.bill_of_materials}"

    @staticmethod
    def is_currency(value: str) -> Tuple[Optional[float], Optional[str]]:
        """ check for currency value assuming symbol is at the start"""
        # regex that looks for a currency symbol then a number with optional decimals
        pattern = r'^([$£€])(\d+(\.\d{1,2})?)$'
        # remove commas - bad for european formatting !!
        value = value.replace(',', '')
        # Match the value with the pattern
        match = re.match(pattern, value)

        if match:
            # Extract symbol and number from the match groups
            symbol = match.group(1)
            number = float(match.group(2))
            return number, symbol
        else:
            return None, None

    def extract_costs(self, data_list: List) -> Tuple:
        """ Tries to find currency column and make a cost table and sub-total for each 'material' """
        items = data_list
        has_currency = False
        currency_column = None
        # Find columns that have currency values and create a costs table
        cost_table = []
        try:
            for item in items:
                for key, value in item.items():
                    number, symbol = self.is_currency(value)
                    if symbol:
                        self.currency_symbol = symbol
                        has_currency = True
                        # if we find a currency column, lets only use that one and block any extra ones
                        if not currency_column:
                            currency_column = key
                        if number is not None:
                            if key == currency_column:
                                cost_table.append({'item_name': item['item_name']} | {'Cost': number, 'Currency': symbol})
                    # reset currency column in case tables have different column names
                    currency_column = None

            if has_currency:
                sub_tot = 0
                for item in cost_table:
                    sub_tot += item['Cost']
                return cost_table, sub_tot
            else:
                return [], 0
        except Exception as e:
            print(f'Error in parsing table for currency values. Error: {e}')
            return [], 0

    def make_bom(self) -> Dict:
        """ complies tables into a bill of materials for rendering"""

        try:
            # build up a set of materials to fill up our bom with
            indices = set()

            for table in self.tables:
                header, data = table
                index, *_ = header
                # check if the table actuall has data, if not don't bother with adding it to the bom
                if data:
                    indices.add(index)

            bom = {index: {'items': [], 'sub_total': 0.0} for index in indices}
        except Exception as e:
            raise Exception(f'BOM Structure Error: {e}')

        try:
            # add a list of rows to our bom to make it easier on our template.
            for table in self.tables:
                header, data = table

                if data:
                    index, *attrs = header
                    for row in data:
                        name, *vals = row
                        bom[index]['items'].append({'item_name': name} | {a: v for a, v in zip(attrs, vals)})

            for material, mat_bom in bom.items():
                cost_table, sub_total = self.extract_costs(mat_bom['items'])
                if cost_table:
                    bom[material]['cost_table'] = cost_table
                    bom[material]['sub_total'] = sub_total
                    self.total_cost += sub_total
        except Exception as e:
            raise Exception(f'Something went wrong setting up the data from the tables {e}')
        return bom


class BOMRenderer:
    """ simple text renderer using our TableBOM class"""
    def __init__(self,
                 bom: TableBOM,
                 template: str = 'project_summary_template'):
        self.bom = bom
        self.template_name = template
        self.env = Environment(loader=PackageLoader('reporter_cli', 'templates'),
                               autoescape=select_autoescape())
        self.template = self.env.get_template(self.template_name)
        self.output = self.make_report()

    def make_report(self) -> str:
        """ renders a bill of materials object with a jinja2 template"""
        try:
            max_len = [[b['item_name'] for b in v['items']] for a, v in self.bom.bill_of_materials.items()]

            if max_len:
                width = max([max([len(item_name) for item_name in col]) for col in max_len])
            else:
                width = 10

            return self.template.render(bom=self.bom.bill_of_materials,
                                        title=self.bom.project_name,
                                        total_cost=self.bom.total_cost,
                                        currency=self.bom.currency_symbol,
                                        max_len=width)
        except Exception as e:
            print(f'Error with template rendering: {e}')
            return ''

    def write_file(self, output_file):
        """ writes output file """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(self.output)
                print(f'{output_file} written successfully')
        except IOError as e:
            print(f"Error writing to file {output_file}: {e}")
