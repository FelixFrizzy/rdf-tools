import argparse
from rdflib import Graph, Namespace, URIRef, RDF
from os.path import splitext

def filter_skos(input_file, output_file, top_concept_uri):
    """
    arguments:
    - input_file (required): path to input file in SKOS rdf/xml (other serializations are untested but might work), e.g. "files/input.rdf"
    - output_file (required): path for output file, e.g. "files/output.pdf"
    - top_concept_uri (required): URI of desired to concept

    return:
        None

    description:
    - goal:
        only keep all concepts of a skos hierarchy that are either
        - ancestors or descendants of the specified top concept (also valid for collections related via skos:broader and skos:narrower)
        - ancestors or descendants of concepts that are related to the top concept by skos:member 
    - steps:
        - find all ancestors and descendants of specified top concept and add them to list
        - do same with collections
        - find all skos:member related concepts, find their ancestors and descendants and add them to the list
        - go through hierarchy and remove all concepts / collections that are not in list
    comments:
    - it keeps skos:collections if they have "skos:broader" to one of the concepts to keep or the top concept itself even though broader/narrower is not allowed by SKOS (see 9.6.4 in https://www.w3.org/TR/skos-reference/#collections)
    """
    skos = Namespace("http://www.w3.org/2004/02/skos/core#")
    # find narrower concepts recursively
    def find_narrower(graph, concept, concepts_to_keep):
        for s, p, o in graph.triples((None, skos["broader"], concept)):
            concepts_to_keep.add(s)
            find_narrower(graph, s, concepts_to_keep)

    # find broader concepts recursively
    def find_broader(graph, concept, concepts_to_keep):
        for s, p, o in graph.triples((concept, skos["broader"], None)):
            concepts_to_keep.add(o)
            find_broader(graph, o, concepts_to_keep)
   
    # New function to find members of a collection recursively
    def find_collection_members(graph, collection, concepts_to_keep):
        for _, _, member in graph.triples((collection, skos["member"], None)):
            concepts_to_keep.add(member)  # Add the member to concepts to keep
            find_narrower(graph, member, concepts_to_keep)  # Recursively find narrower concepts
            find_broader(graph, member, concepts_to_keep)  # Recursively find broader concepts
            if (member, RDF.type, skos["Collection"]) in graph:  # If the member is also a collection
                find_collection_members(graph, member, concepts_to_keep)  # Recursive call for nested collections

    skos_graph = Graph()
    skos_graph.parse(input_file)



    desired_top_concept = URIRef(top_concept_uri)

    concepts_to_keep = set()
    

    concepts_to_keep.add(desired_top_concept)

    # identify and keep broader terms from desired top conecpts and their ancestors
    find_broader(skos_graph, desired_top_concept, concepts_to_keep)

    # identify and keep narrower concepts from the desired top concept and its children
    find_narrower(skos_graph, desired_top_concept, concepts_to_keep)

    # identify and keep SKOS collections that are 'narrower' or 'broader'
    collections_to_keep = set()
    find_collection_members(skos_graph, desired_top_concept, concepts_to_keep)  # Now also finds nested collection members

    # set to True if all concept schemes should be kept
    # set to False if only schemes associated with the desired top concept should be kept
    keep_all_schemes = True

    if keep_all_schemes:
        # Identify and keep all concept schemes
        schemes_to_keep = set()
        for scheme in skos_graph.subjects(RDF.type, skos["ConceptScheme"]):
            schemes_to_keep.add(scheme)
    else:
    # find only associated schemes 
    # limited to all schemes that are object of a skos:scheme relation in any of the concepts_to_keep
        for concept in concepts_to_keep:
            for s, p, o in skos_graph.triples((concept, skos["inScheme"], None)):
                schemes_to_keep.add(o)  # Add the scheme URIs to the set

    # Merge concepts and collections and schemes to keep
    elements_to_keep = concepts_to_keep.union(collections_to_keep).union(schemes_to_keep)

    # do the actual removal
    for s, p, o in list(skos_graph.triples((None, None, None))):  # Convert to list to avoid modification issues during iteration
        """
        logic explanation
        drop term if:
            term is not in elements_to_keep (this usually only is true for the desired top concept)
            or if
            term has a broader narrower relation and the term it is related to is not in elements_to_keep

        """
        if (s not in elements_to_keep) or (p in [skos["broader"], skos["narrower"]] and o not in elements_to_keep):
            skos_graph.remove((s, p, o))

    # Save the modified SKOS file
    skos_graph.serialize(destination=output_file, format="xml")
    print("saved file as {}".format(output_file))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Filter SKOS hierarchies.')
    parser.add_argument('--input_filename', type=str, required=True, help='The input RDF file path.')
    parser.add_argument('--output_filename', type=str, help='The output RDF file path. Optional; if not provided, defaults to <input_filename>_reduced.rdf')
    parser.add_argument('--top_concept', type=str, required=True, help='The URI of the top concept.')
    
    # Parse the arguments
    args = parser.parse_args()

    # Determine the output filename
    if not args.output_filename:
        root, ext = splitext(args.input_filename)
        output_filename = "{}_reduced{}".format(root, ext)
    else:
        output_filename = args.output_filename

    # Call the function with the specified parameters from command line
    filter_skos(args.input_filename, output_filename, args.top_concept)




