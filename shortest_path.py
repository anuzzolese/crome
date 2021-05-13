from builtins import staticmethod, int

from SPARQLWrapper import SPARQLWrapper
from SPARQLWrapper.Wrapper import TURTLE
from rdflib import Graph
from rdflib.namespace import RDFS
from rdflib.term import URIRef

from typing import List


class Path:
    def __init__(self):
        self.__path = []
        
    def add(self, node : URIRef) -> None:
        
        self.__path.append(node)
        
    def length(self) -> int:
        return len(self.__path)
    
    def contains(self, node : URIRef) -> bool:
        
        return node in self.__path
    
    def shared_subpath(self, node : URIRef) -> List[URIRef]:
        
        ret = []
        if self.contains(node):
            for n in self.__path:
                ret.append(n)
                if n == node:
                    return ret
    
        return ret
    
    def __str__(self):
        content = "["
        first = True
        for node in self.__path:
            if not first:
                content += ', '
            else:
                first = False
            
            content += node.n3()
            
        content += ']'
        
        return content 
    
    
    def __iter__(self):
        return self.__path.__iter__()
    
    def __getitem__(self, x):
        return self.__path.__getitem__(x)
    
    def __len__(self):
        return len(self.__path)
    
class Subtree:
    def __init__(self, root : URIRef, left_branch : Path, right_branch : Path):
        self.__root = root
        self.__left_branch = left_branch
        self.__right_branch = right_branch
        
    def get_root(self):
        return self.__root
    
    def get_left_branch(self):
        return self.__left_branch
    
    def get_right_branch(self):
        return self.__right_branch
    
    def __len__(self):
        return len(self.__left_branch) + len(self.__right_branch)
    
    def __str__(self):
        content = '['
        first = True
        for node in self.__left_branch:
            if not first:
                content += ', '
            else:
                first = False
            
            content += node.n3()
            
        content += '] ' + self.__root.n3()
        
        content += ' ['
        first = True
        for node in self.__right_branch:
            if not first:
                content += ', '
            else:
                first = False
            
            content += node.n3()
            
        content += ']'
        
        return content
    
    
    
class Subtrees:
    
    def __init__(self):
        self.__subtrees = []
        
    def add(self, subtree : Subtree) -> None:
        
        self.__subtrees.append(subtree)
        
    def __str__(self):
        content = ''
        for subtree in self.__subtrees:
            if content != '':
                content += '\n'
            content += str(subtree)
            
        return content

    def __iter__(self):
        return self.__subtrees.__iter__()
    
    def min(self):
        min_subtrees = None
        
        for subtree in self.__subtrees:
            if not min_subtrees:
                min_subtrees = Subtrees()
                min_subtrees.add(subtree)
            else:
                min_subtree = min_subtrees[0]
                if len(subtree) < len(min_subtree):
                    min_subtrees = Subtrees()
                    min_subtrees.add(subtree)
                elif len(subtree) == len(min_subtree):
                    min_subtrees.add(subtree)
                    
        return min_subtrees 
    
    def __getitem__(self, x):
        return self.__subtrees.__getitem__(x)
    
    
class Paths:
    
    def __init__(self):
        self.__paths = []
        
    def add(self, path : Path) -> None:
        
        self.__paths.append(path)
        
    def join(self, paths) -> Subtree:
        subtrees = Subtrees()
        for left_path in self.__paths:
            on_left = left_path[-1]
            for right_path in paths:
                on_right = right_path[-1]
                if on_left == on_right:
                    
                    left_branch_path = Path()
                    right_branch_path = Path()
                    for elem in [e for e in left_path[:-1]]:
                        left_branch_path.add(elem)
                    for elem in [e for e in right_path[-2::-1]]:
                        right_branch_path.add(elem)
                    
                    subtrees.add(Subtree(on_left, left_branch_path, right_branch_path))
        
        return subtrees
                    

    def __str__(self):
        content = ''
        for path in self.__paths:
            if content != '':
                content += '\n'
            content += str(path)
            
        return content

    def __iter__(self):
        return self.__paths.__iter__()
    

class ShortestPathFinder:
    
    def __init__(self):
        self.__graph = Graph()
        
        
    def find(self, start: URIRef, end: URIRef):
        
        
        g = self.__query(start, end)
        
        paths_left = self.find_hierarchy(start, g=g)
        paths_right = self.find_hierarchy(end, g=g)
        
        subtrees = paths_left.join(paths_right)
        return subtrees.min()
        

        
    def find_hierarchy(self, start: URIRef, path_: Path = None, paths : Paths = None, g : Graph = None) -> List[Path]:
        
        if not g:
            g = self.__graph
        
        current = start
        
        if not path_:
            path_ = Path()
            
        path_.add(current)
        
        if not paths:
            paths = Paths()
            
        paths.add(path_)
        
        
        destinations = [o for o in g.objects(current, RDFS.subClassOf)]
        
        if destinations and len(destinations) > 0:
            for destination in destinations:
                
                path_aux_ = Path()
                
                for path_element in path_:
                    path_aux_.add(path_element)
                
                self.find_hierarchy(destination, path_aux_, paths, g)
             
                
        return paths
    
    
    def __query(self, concept_1 : URIRef, concept_2 : URIRef) -> Graph:
        # We provide the system with the address the SPARQL endpoint is located in.
        endpoint = SPARQLWrapper("http://localhost:8890/sparql/")

        # We define our SPARQL query (cf. examples).
        '''
        sparql = """
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                CONSTRUCT {
                    ?mid rdfs:subClassOf ?o
                }
                WHERE {
                GRAPH <snomed-ligth> {
                    {
                        %s rdfs:subClassOf*|(owl:intersectionOf/rdf:rest*/rdf:first)* ?mid . 
                        ?mid rdfs:subClassOf|(owl:intersectionOf/rdf:rest*/rdf:first) ?o
                    }
                    UNION
                    {
                        %s rdfs:subClassOf*|(owl:intersectionOf/rdf:rest*/rdf:first)* ?mid . 
                        ?mid rdfs:subClassOf|(owl:intersectionOf/rdf:rest*/rdf:first) ?o 
                    }
                    FILTER(ISIRI(?o))
                    FILTER(ISIRI(?mid))
                }}
                """%(concept_1.n3(), concept_2.n3())
        '''
        sparql = """
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                CONSTRUCT {
                    ?mid rdfs:subClassOf ?o
                }
                WHERE {
                    GRAPH <snomed-light> {
                        %s rdfs:subClassOf* ?mid . 
                        ?mid rdfs:subClassOf ?o
                        FILTER(ISIRI(?o))
                        FILTER(ISIRI(?mid))
                    }
                }
                """

        graph = Graph()
        concepts = [concept_1.n3(), concept_2.n3()]
        
        for c in concepts:
                
            # We configure the endpoint in order to execute our SPARQL query.
            endpoint.setQuery(sparql%c)
    
            # We configure the endpoint in order to have the results serialised with JSON as output.
            endpoint.setReturnFormat(TURTLE)
            result = endpoint.query().convert()
        
        
        
            g = Graph()
            g.parse(data=result, format="turtle")
            
            graph += g
        
        return graph
        
    
if __name__ == '__main__':
    spf = ShortestPathFinder()
    
    min_subtrees = spf.find(URIRef('http://snomed.info/id/191629006'), URIRef('http://snomed.info/id/38451003'))
    
    for min_subtree in min_subtrees:
        
        shared_concept = min_subtree.get_root()
        left_subtree = min_subtree.get_left_branch()
        right_subtree = min_subtree.get_right_branch()
        
        print('- Solution with path length %d'%(len(min_subtree)))
        print('\t Min shared ancestor %s'%(shared_concept)) # Il genitore comune
        print('\t Left branch with length %d: %s'%(len(left_subtree), left_subtree)) # Il ramo sinistro che va dal primo concetto verso il genitore comune
        print('\t Right branch with length %d: %s'%(len(right_subtree), right_subtree)) # Il ramo destro che va dal genitore comune verso il secondo concetto
    
    