from pathlib import Path
import os
import re
from typing import Tuple, List, Dict
from jinja2 import Environment, FileSystemLoader, select_autoescape, PackageLoader

class TextProcessor:
    def __init__(self,
                 filename: str):
        self.filename = Path(filename)
        self.text = self._read_file()
        self.project_name = None
        self.tables = self.extract_tables()

    def _read_file(self):
        with self.filename.open('r', encoding='utf-8') as f:
            return f.read()


    def _process_table(self,table: List) -> Tuple[List, List]:
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
            print('Could not extract tables from provided text')
        return tables


class TableBOM:

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
    def is_currency(value: str) -> Tuple:
        # Check if the value matches a currency pattern for $, £, or €
        match = re.match(r'^(?P<symbol>[\$\£\€])(?P<number>\d+(\.\d{1,2})?)$', value)
        if match:
            return float(match.group('number')), match.group('symbol')
        else:
            return None, None

    def extract_and_sum_currency(self, data_list: List) -> Tuple:
        items = data_list
        has_currency = False
        # Find columns that have currency values and create a costs table
        cost_table = []
        try:
            for item in items:

                for key, value in item.items():
                    if has_currency:
                        continue
                    number, symbol = self.is_currency(value)
                    if symbol:
                        self.currency_symbol = symbol
                        has_currency = True
                    if number is not None:
                        cost_table.append({'item_name':item['item_name']} | {'Cost': number,'Currency': symbol})

            if has_currency:
                sub_tot = 0
                for item in cost_table:
                    sub_tot += item['Cost']
                return cost_table,sub_tot
            else:
                return [], 0
        except Exception as e:
            print('Error in parseing table for currency values')
            return [], 0

    def make_bom(self) -> Dict:
        indices = set()
        try:
            for table in self.tables:
                header, _ = table
                index, _ = header
                indices.add(index)

            bom = {index: {'items': [], 'sub_total': 0.0} for index in indices}
        except Exception as e:
            raise Exception(f'BOM Structure Error: {e}')
        try:
            for table in self.tables:
                header, data = table
                index, *attrs = header
                for row in data:
                    name, *vals = row
                    bom[index]['items'].append({'item_name': name} | {a: v for a, v in zip(attrs, vals)})

            for material, mat_bom in bom.items():
                cost_table,sub_total = self.extract_and_sum_currency(mat_bom['items'])
                if cost_table:
                    bom[material]['cost_table'] = cost_table
                    bom[material]['sub_total'] = sub_total
                    self.total_cost += sub_total
        except Exception as e:
            raise Exception(f'Something went wrong setting up the data from the tables {e}')
        return bom


class BOMRenderer:

    def __init__(self,
                 bom: TableBOM,
                 template: str = 'project_summary_template',):
        self.bom = bom
        self.template_name = template
        self.env = Environment(loader=PackageLoader('reporter_cli', 'templates'),
                               autoescape=select_autoescape())
        self.template = self.env.get_template(self.template_name)
        self.output = self.make_report()

    def make_report(self) -> str:
        try:
            max_len = [[b['item_name'] for b in v['items']] for a,v in self.bom.bill_of_materials.items()]

            if max_len:
                width = max([max([len(s) for s in l]) for l in max_len])
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

    def write_file(self,output_file):
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(self.output)
                print(f'{output_file} written successfully')
        except IOError as e:
            print(f"Error writing to file {output_file}: {e}")
