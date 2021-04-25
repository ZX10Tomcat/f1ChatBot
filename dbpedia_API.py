from SPARQLWrapper import SPARQLWrapper, JSON


def dbpedia_get_hometown(driver_name):

    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    query = """PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>       
        PREFIX type: <http://dbpedia.org/class/yago/>
        PREFIX dbp: <http://dbpedia.org/property/>
        
        SELECT ?birthPlace
        WHERE { 
            ?person a dbo:Person .
            {?person rdfs:label "{driver_name}"@en}
            OPTIONAL { ?person dbo:birthPlace ?bp . ?bp rdfs:label ?birthPlace. }
            FILTER (LANG(?birthPlace)='en')
        }
        Limit 1"""

    placed_query = query.replace("{driver_name}", driver_name)
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery(placed_query)
    
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return results["results"]["bindings"][0]["birthPlace"]["value"]