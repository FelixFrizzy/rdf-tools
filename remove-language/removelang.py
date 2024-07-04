import argparse
from rdflib import Graph, Namespace, URIRef, RDF, Literal
from os.path import splitext



def filter_language(input_file, output_file, languages, keep_other_lang):
    """
    Filters SKOS concepts based on language preferences, retaining hierarchical relationships.

    This function parses a SKOS RDF/XML file and creates a new file where only the concepts that have a prefLabel 
    in the specified language and their hierarchical parents are retained. 
    Depending on the keep_other_lang flag, it either keeps or removes all literals not in the specified languages.

    Args:
        input_file (str): Path to the input RDF/XML file containing the original SKOS data.
        output_file (str), optional: Path for the output RDF/XML file to be saved after language filtering.
        (multiple) languages (str): ISO 639-1 language codes representing the languages to retain.
                                 Multiple languages need to be seperated with a single whitespace.
                                 Example: en es for English and Spanish.
        keep_other_lang (bool): A flag indicating whether to retain (True) or remove (False) prefLabels in languages
                                other than those specified. When True, prefLabels in non-specified languages are kept;
                                when False, they are removed, except for those attached to kept concepts.

    Returns:
        None. The function outputs a new RDF/XML file at the location specified by the `output_file` argument.

    Side effects:
        Setting keep_other_lang to False can result in terms having no label at all.

    Example Usage:
    - call function in python:
        filter_language("input.rdf", "output.rdf", ["en", "fr"], False)
    - call function from command line:
        python3 removelang.py --input_filename "input.rdf" --output_filename "output.rdf" --languages en es --keep_other_lang False
        This will process 'input.rdf', removing all concepts that do not have English or French prefLabels,
        removing all non-English and non-French literals from retained concepts, and save the result to 'output.rdf'.
    """

    skos = Namespace("http://www.w3.org/2004/02/skos/core#")

    # find broader concepts recursively
    def find_broader(graph, concept, concepts_to_keep):
        for s, p, o in graph.triples((concept, skos["broader"], None)):
            concepts_to_keep.add(o)
            find_broader(graph, o, concepts_to_keep)


    skos_graph = Graph()
    skos_graph.parse(input_file)
    
    concepts_to_keep = set()

    # Find all terms with a preferred label in specified languages and their parents
    for term, _, _ in skos_graph.triples((None, skos["prefLabel"], None)):
        for _, _, label in skos_graph.triples((term, skos["prefLabel"], None)):
            if label.language in languages:
                concepts_to_keep.add(term)
                find_broader(skos_graph, term, concepts_to_keep)

    

    # do the acutal removal
    """
    logic explanation
    drop term if:
        term is not in concepts_to_keep (this usually only is true for the desired top concept)
        or if
        term has a broader narrower relation and the term it is related to is not in concepts_to_keep
    if keep_other_lang is set to False:
        remove pref:labels in concepts_to_keep in all other languages but the selected one(s)
    """
    for s, p, o in list(skos_graph.triples((None, None, None))):  # Convert to list to avoid modification issues during iteration
        if (s not in concepts_to_keep) or (p in [skos["broader"], skos["narrower"]] and o not in concepts_to_keep):
            skos_graph.remove((s, p, o))

        # only executed for concepts_to_keep
        
        # # only removes prefLabels in another language
        # # this leads to concepts having no label at all
        # elif not keep_other_lang: 
        #     if p == skos["prefLabel"] and s in concepts_to_keep and o.language not in languages:
        #     # Additionally remove prefLabels in languages not specified to keep
        #         skos_graph.remove((s, p, o))

        # removes all objects containing a language tag in another language
        # this leads to concepts having no label at all
        elif not keep_other_lang:
            if isinstance(o, Literal) and s in concepts_to_keep and o.language and o.language not in languages:
            # Additionally remove prefLabels in languages not specified to keep
                skos_graph.remove((s, p, o))


    # Save the modified SKOS file
    skos_graph.serialize(destination=output_file, format="xml")
    print("saved file as {}".format(output_file))





if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter SKOS labels based on language, keeping term hierarchies and retaining all related information.")
    parser.add_argument('--input_filename', type=str, required=True, help='Input RDF/XML file')
    parser.add_argument('--output_filename', type=str, help='Output RDF/XML file')
    parser.add_argument('--languages', nargs='+', required=True, help='List of language tags to keep')
    parser.add_argument('--keep_other_lang', type=str, choices=['True', 'False'], nargs='?', const='True', default='True', help='Whether to retain prefLabels in languages other than the specified ones, can be "True" or "False"' )
    args = parser.parse_args()
    # convert argparse string to bool
    args.keep_other_lang = args.keep_other_lang == 'True'

    # Determine the output filename
    if not args.output_filename:
        root, ext = splitext(args.input_filename)
        if args.keep_other_lang:
            output_filename = f"{root}_{'_'.join(args.languages)}{ext}" # this results in original file name with all languages appended
        else:
            output_filename = f"{root}_{'_'.join(args.languages)}_only{ext}" # this results in original file name with all languages appended

    else:
        output_filename = args.output_filename

    filter_language(args.input_filename, output_filename, args.languages, args.keep_other_lang)
