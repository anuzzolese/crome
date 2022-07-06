from jinja2 import Environment, FileSystemLoader, Template
from pyrml import TermUtils, RMLConverter
import unidecode, re
from rdflib import Graph, Namespace
from rdflib.parser import StringInputSource
from lark import Lark
from lark.visitors import Transformer
import hashlib

def digest(s):
	hash = hashlib.md5(s.encode()) 
	return hash.hexdigest()
	
def age(val):
    return int(float(val.replace(" year", "")))
    
def age_value(val):
    return int(float(val.split(" ")[0]))
    
def age_unit(val):
    return val.split(" ")[1]
    
def id(val):
	return TermUtils.generate_id(val)
 
def solver_type(type, cond):
	
	if cond == 'uri':
		if type.startswith("CI["):
			print("algorithm")
			return 'algorithm'
		else: 
			print("human")
			return 'human'
	else:
		if type.startswith("CI["):
			return 'Algorithm'
		else: 
			return 'Human'
			
def solver_solve_number(solve_num, solver_id, case_id):
	return digest(solve_num+solver_id+case_id)
	

def gender(val):
    if val == "M":
        return "male"
    elif val == "F":
        return "female"
    else: 
        return val
    
def follows(item):
    item = int(item)
    return (item-1) if item>1 else None
    
def case_type_id(gmr):
    gmr = gmr.strip()
    if gmr == "Y":
        return "validated-case"
    else:
        return "not-validated-case"
        
        
def case_type(gmr):
    gmr = gmr.strip()
    if gmr == "Y":
        return "Validated case."
    else:
        return "Not-validated case."
        
def case_category_id(row):
    if row["Is Case IM"].strip() == "Y":
        return "internal-medicine"
    elif row["Is Case Surg"].strip() == "Y":
        return "surgery"
    else:
    	return "other"
    	
def case_category(row):
    if row["Is Case IM"].strip() == "Y":
        return "Internal medicine."
    elif row["Is Case Surg"].strip() == "Y":
        return "Surgery."
    else:
    	return "Other."
    	
def get_solution(row):
    if row["Is Case IM"].strip() == "Y":
        return "internal-medicine"
    elif row["Is Case Surg"].strip() == "Y":
        return "surgery"
    else:
    	return "other"

if __name__ == '__main__':
	file_loader = FileSystemLoader('.')
	env = Environment(loader=file_loader)
	template = env.get_template('answer_clusters copy.ttl')
	rml_mapping = template.render(csv="../human-dx-data-sharing-crome/solves.tsv")
	#rml_mapping = template.render(csv="./humandx-test.tsv")

	rml_converter = RMLConverter()
	rml_converter.register_fucntion("digest", digest)
	rml_converter.register_fucntion("age_value", age_value)
	rml_converter.register_fucntion("age_unit", age_unit)
	rml_converter.register_fucntion("generate_id", id)
	#rml_converter.register_fucntion("age", age)
	rml_converter.register_fucntion("gender", gender)
	rml_converter.register_fucntion("case_type_id", case_type_id)
	rml_converter.register_fucntion("case_type", case_type)
	rml_converter.register_fucntion("case_category_id", case_category_id)
	rml_converter.register_fucntion("case_category", case_category)
	rml_converter.register_fucntion("get_solution", get_solution)
	rml_converter.register_fucntion("solver_type", solver_type)
	rml_converter.register_fucntion("solver_solve_number", solver_solve_number)

	rdf = StringInputSource(rml_mapping.encode('utf-8'))
	#print(rml_mapping.encode('utf-8'))

	g = rml_converter.convert(rdf)

	g.bind("crome", Namespace("https://w3id.org/stlab/crome/ontology/"))    
	g.serialize(destination="crome-kg.nt", format="nt")
