from rdflib import Graph, URIRef
from collections import Counter
import re

def find_urispace(data, extension):
    """
    finds URISpace of SKOS file
    input: data and file extension, only allowed is rdf or ttl
    returns: most common base URI, if multiple are found, the first one is returned, if nothing is found, None is returned
    """
    
    g = Graph()
    if extension == 'rdf':
        g.parse(data, format="xml")
    elif extension == 'ttl':
        g.parse(data, format="ttl")
    else:
        raise ValueError('invalid format')

    # Create a dictionary of all namespace prefixes to their full URIs
    namespace_map = {prefix: str(ns) for prefix, ns in g.namespaces()}


    # Collect all URIs directly from subjects, expand prefixed URIs
    uris = []
    for subject in g.subjects():
        # Only consider subject of type URIRef
        if isinstance(subject, URIRef):
            # Convert URIRef to a string for processing
            uri_str = str(subject)
            # Check if the URI contains a namespace prefix that needs expansion
            # URIs without prefix typically contain '//' but no ':' from http:// or https://
            if ':' in uri_str and '//' not in uri_str:
                # Attempt to expand based on namespace prefix
                prefix, local_part = uri_str.split(':', 1)
                if prefix in namespace_map:
                    # Use the dictionary to expand the prefix
                    uri_str = namespace_map[prefix] + local_part
            uris.append(uri_str)



    # Use regular expressions to extract the base URI from each full URI
    # finds URIs with up to 4 slashes after the domain name
    # can be adjusted in the {1,4} part
    pattern = re.compile(r'(https?://[^/]+(?:/[^/]+){0,4}/)')
    uri_prefixes = [pattern.match(uri) for uri in uris]
    uri_prefixes = [match.group(1) for match in uri_prefixes if match]

    # Count occurrences of each base URI and find the most common
    prefix_count = Counter(uri_prefixes)
    most_common_prefix = prefix_count.most_common(1)

    # Return the most common base URI
    if most_common_prefix:
        print("Urispace found: {urispace}".format(urispace=most_common_prefix[0][0]))
        return(most_common_prefix[0][0])
    else:
        return None


# Replace 'path_to_your_file.rdf' with the path to your RDF/XML file
find_urispace('path_to_your_file.rdf', 'rdf')
