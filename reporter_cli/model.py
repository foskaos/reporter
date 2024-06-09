from pathlib import Path
import os
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

    def _process_table(self,
                       table: List) -> Tuple[List, List]:
        header = [cell.strip() for cell in table[0].split('|') if cell.strip()]
        data = []
        for row in table[2:]:
            cells = [cell.strip() for cell in row.split('|') if cell.strip()]
            if len(cells) == len(header):
                data.append(cells)

        return header, data

    def extract_tables(self) -> List:
        tables = []
        current_table = []
        inside_table = False

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

        return tables


class TableBOM:

    def __init__(self,
                 tables: list,
                 project_name: str):
        self.tables = tables
        self.total_cost = 0.0
        self.bill_of_materials = self.make_bom()
        self.project_name = project_name


    def __repr__(self):
        return f"{self.bill_of_materials}"

    def make_bom(self) -> Dict:
        indices = set()
        for table in self.tables:
            header, _ = table
            index, _ = header
            indices.add(index)

        bom = {index: {'items': [], 'sub_total': 0.0} for index in indices}

        for table in self.tables:
            header, data = table
            index, *attrs = header
            for row in data:
                name, *vals = row
                bom[index]['items'].append({'model_name': name} | {a: v for a, v in zip(attrs, vals) if a in ['Price']})

        for material, mat_bom in bom.items():
            for item in mat_bom['items']:
                if 'Price' in item.keys():
                    bom[material]['sub_total'] += float(item['Price'][1:])
                    self.total_cost += float(item['Price'][1:])

        return bom


class BOMRenderer:

    def __init__(self,
                 bom: TableBOM,
                 template: str = 'project_summary_template',
                 template_dir: str = 'reporter_cli/templates'):
        self.bom = bom
        self.template_name = template
        self.env = Environment(loader=PackageLoader('reporter_cli', 'templates'),#loader=FileSystemLoader("reporter_cli/templates"),
                               autoescape=select_autoescape())
        self.template = self.env.get_template(self.template_name)
        self.output = self.make_report()

    def make_report(self) -> str:
        max_len = [[b['model_name'] for b in v['items']] for a,v in self.bom.bill_of_materials.items()]

        if max_len:
            width = max([max([len(s) for s in l]) for l in max_len])
        else:
            width = 10
        return self.template.render(bom=self.bom.bill_of_materials,
                                    title=self.bom.project_name,
                                    total_cost=self.bom.total_cost,
                                    max_len=width)

    def write_file(self,output_file):
        with open(output_file,'w') as f:
            f.write(self.output)
            print(f'{output_file} written successfully')







