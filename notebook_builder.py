import json
import os
import copy
from typing import Dict, List

class Cell():
    def __init__(self, cell_type: str, id: str, metadata: Dict, source: List[str], **kwargs) -> None:
        self.cell_type = cell_type
        self.execution_count = None
        if self.cell_type == 'code':
            self.execution_count = kwargs['execution_count']
        self.id = id
        self.metadata = metadata
        self.source_code = source

    def __repr__(self) -> str:
        return f'Cell(id={self.id}, cell_type={self.cell_type})'

    @property
    def _to_dict(self):
        new_dict = {'cell_type': self.cell_type}
        if self.cell_type == 'code':
            new_dict['execution_count'] = self.execution_count
        new_dict['id'] = self.id
        new_dict['metadata'] = self.metadata
        new_dict['source'] = self.source_code
        return new_dict

    def __str__(self) -> str:
        return str(self._to_dict)
        

class Notebook():
    def __init__(self, path: str, load=False, **kwargs) -> None:
        self.cells = [] if 'cells' not in kwargs else kwargs['cells']
        self.metadata = {} if 'metadata' not in kwargs else kwargs['metadata']
        self.nbformat = 4
        self.nbformat_minor = 5
        if load:
            if os.path.isfile(path) and path.endswith('.ipynb'):
                self.path = path
                print("Loading existent notebook...")
                with open(self.path) as file:
                    full_json = json.load(file)

                    # Load cells:
                    for cell_info in full_json['cells']:
                        cell = Cell(**cell_info)
                        self.cells.append(cell)
                    
                    # Load notebook metadata:
                    self.metadata = full_json['metadata']
        else:
            # print("Creating new Notebook instance from zero...")
            new_path = path if path.endswith('.ipynb') else path + '.ipynb'
            self.path = new_path
        

    def append(self, other, new_path=None):
        new_cells = self.cells + other.cells
        return Notebook(path=new_path if new_path is not None else self.path, load=False, cells=new_cells, metadata=self.metadata)

    def __repr__(self) -> str:
        return f"Notebook(path={self.path}, ncells={len(self.cells)})"
    
    @property
    def cells_to_list(self) -> List:
        """
            Converts each cell to its dict version.

        Returns:
            new_list: a list, the strings that represents the notebook cells.
        """
        new_list = []
        for cell in self.cells:
            new_list.append(cell._to_dict)
        return new_list

    def save(self, path: str = None):
        """Saves the Jupyter Notebook"""
        new_dict = {'cells': self.cells_to_list, 'metadata': self.metadata, 'nbformat': self.nbformat,
                    'nbformat_minor': self.nbformat_minor}
        with open(self.path if path is None else path, "w") as outfile: 
            json.dump(new_dict, outfile)
        

class ModularTemplate(Notebook):
    def __init__(self, path: str, load=True, **kwargs) -> None:
        """_summary_

        Args:
            path (str): the path of the notebook.
            load (bool, optional): wether to load the notebook from the path or not. Defaults to True.
        """
        super().__init__(path, load, **kwargs)

    def build_modular_notebook(self, path: str, modular_titles: List[str], modular_key_word: str = 'modular-word'):
        """
        Repeats the modular section len(modular_words) times, and appends init and end section.

        Args:
            modular_titles (List[str]): the titles that will replace the modular_key_word inside a modular section.
            modular_key_word (str): the key workd to be replaced inside the template.
        """
        for i, cell in enumerate(self.cells):
            if cell.cell_type == 'markdown':
                if '[start-modular-section]' in cell.source_code[0]:
                    start = i + 1
                elif '[end-modular-section]' in cell.source_code[0]:
                    end = i 
        init_cells = self.cells[:start-1] # start-1 skips the markdown that says "init-modular-section"
        end_cells = self.cells[end+1:] # end+1 skips the markdown that says "end-modular-section"


        notebook_start = Notebook(path, load=False, cells=init_cells)
        # Build a small notebook for each modular section and appends successively to notebook start:
        for word in modular_titles:
            modular_section = self.cells[start:end]
            replaced_modular_cells = []
            for cell in modular_section:
                new_cell = copy.deepcopy(cell)
                # Replace word on each line inside the source code:
                new_lines = []
                for line in new_cell.source_code:
                    line = line.replace(modular_key_word, word)
                    new_lines.append(line)
                # Save the new lines inside the Cell instance:
                new_cell.source_code = new_lines
                # Append the whole cell:
                replaced_modular_cells.append(new_cell)
            small_notebook = Notebook(path, load=False, cells=replaced_modular_cells)
            notebook_start = notebook_start.append(small_notebook)
        
        # Appends the last section:
        notebook_end = Notebook(path, load=False, cells=end_cells)
        notebook_start = notebook_start.append(notebook_end)

        return notebook_start

