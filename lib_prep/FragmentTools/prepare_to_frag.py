#!/usr/bin/env python
"""
Program to prepare FragPELE instruction's from PDB libraries.
"""

import os
import argparse
from string import Template

from rdkit import Chem
from lib_prep.LibraryManager import lib_manager
from lib_prep import pdb_modifier

__author__ = "Carles Perez Lopez"
__version__ = "1.1.0"
__maintainer__ = "Carles Perez Lopez"
__email__ = "carlesperez94@gmail.com"

#Path variables
module_path = os.path.abspath(os.path.dirname(pdb_modifier.__file__))
global_lib_path = os.path.join(module_path, "Libraries/global")

def parse_arguments():
    """
        Parse user arguments
        Output: list with all the user arguments
    """
    # All the docstrings are very provisional and some of them are old, they would be changed in further steps!!
    parser = argparse.ArgumentParser(description="""Description: Program to prepare FragPELE instruction files 
    from PDB libraries.""")
    required_named = parser.add_argument_group('required named arguments')
    required_named.add_argument("pdb_complex", type=str, help="Path to core or scaffold PDB complex.")
    required_named.add_argument("heavy_atom_pdb_complex", type=str, help="PDB atom name of the heavy atom of the core "
                                                                         "or scaffold PDB complex that is used to"
                                                                         " grow the fragments of the library onto it.")
    parser.add_argument("-l", "--lib_path", type=str, default=global_lib_path,
                        help="Path to the library (folder) which must contain"
                             "PDB files with the fragments.")
    parser.add_argument("-m", "--mode", type=str, default="first-occurrence", choices=["first-occurrence"],
                        help="Criteria to select atoms of fragments to connect with the heavy atom of the complex."
                             "Currently only 'first-ocurrence' is available: the first HvA found with a at least one"
                             "hydrogen atom is selected.")
    parser.add_argument("-o", "--out", type=str, default=None,
                        help="If selected, path to the file with the instructions to run FragPELE.")
    parser.add_argument("--global_lib", action='store_true',
                        help="Set this flag to prepare FragPELE configuration files to run the global library.")

    args = parser.parse_args()

    return args.pdb_complex, args.heavy_atom_pdb_complex, args.lib_path, args.mode, args.out, args.global_lib


class FragPreparator(lib_manager.LibraryChecker):
    def __init__(self, pdb_complex, heavy_atom_pdb_complex, library_path, mode="first-occurrence", instructions=None):
        self.pdb_complex = pdb_complex
        self.heavy_atom_pdb_complex = heavy_atom_pdb_complex
        self.path_to_library = library_path
        self.mode = mode
        self.library_files = lib_manager.LibraryChecker.get_files(self)
        self.instructions = instructions

    def select_atom_to_grow(self, pdb_file):
        mol = Chem.MolFromPDBFile(pdb_file)
        if self.mode == "first-occurrence":
            for atom in mol.GetAtoms():
                if atom.GetTotalNumHs() > 0 and not atom.GetSymbol == "H":
                    idx = atom.GetIdx()
                    print("Atom {} Found".format(idx+1))
                    return idx+1   # The atom 0 for rdkit is the atom 1 in a PDB file

    def prepare_frag_pele_instructions(self):
        instructions = []
        lib_manager.LibraryChecker.check_library_format(self)
        for pdb in self.library_files:
            try:
                atom_idx = self.select_atom_to_grow(pdb)
                pdb_obj = pdb_modifier.PDB(pdb)
                instruction_line = "{}   {}  {}".format(os.path.abspath(pdb), self.heavy_atom_pdb_complex,
                                                        pdb_obj.find_pdb_atom_name_of_idx(atom_idx).strip())
                print(instruction_line)
                instructions.append(instruction_line)
            except Exception as e:
                print(e)
        self.instructions = "\n".join(instructions)
    
    def write_instructions_to_file(self, out_file=None):
        if not out_file:
            out_file = os.path.join(self.path_to_library,
                                    "serie_file_{}.conf".format(os.path.basename(os.path.splitext(self.pdb_complex)[0])))
        with open(out_file, "w") as out:
            out.write(self.instructions)
        print("Serie file saved in {}".format(out_file))


    def prepare_global_lib(self):
        template_glob = os.path.join(module_path, "Templates", "global_template.conf")
        with open(template_glob) as t:
            template = t.read()
        temp_obj = Template(template)
        result = temp_obj.safe_substitute({"ATOM": self.heavy_atom_pdb_complex, "PATH": self.path_to_library})
        self.instructions = result


def main(pdb_complex, heavy_atom_pdb_complex, lib_path, mode="first-occurrence", out_file=None, global_lib=False):
    prepare_fragpele = FragPreparator(pdb_complex=pdb_complex, heavy_atom_pdb_complex=heavy_atom_pdb_complex,
                                      library_path=lib_path, mode=mode)
    if global_lib:
        prepare_fragpele.prepare_global_lib()
    else:
        prepare_fragpele.prepare_frag_pele_instructions()
    prepare_fragpele.write_instructions_to_file(out_file)


if __name__ == '__main__':
    pdb_complex, heavy_atom_pdb_complex, library_path, mode, out, global_lib = parse_arguments()
    main(pdb_complex, heavy_atom_pdb_complex, library_path, mode, out, global_lib)


