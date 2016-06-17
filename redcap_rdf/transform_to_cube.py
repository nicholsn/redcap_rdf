##
##  See COPYING file distributed along with the redcap_rdf package for the
##  copyright and license terms
##
""" Data Dictionary Transformer to Semantic

@author: Victor Meyerson
"""
import os
import csv
import hashlib

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, FOAF, RDF, RDFS, OWL, SKOS, VOID, XSD

from redcap_rdf.util import log

# Header columns for data dictionary
FIELD_NAME = "Variable / Field Name"
FORM = "Form Name"
FIELD_TYPE = "Field Type"
FIELD_LABEL = "Field Label"
CHOICES = "Choices, Calculations, OR Slider Labels"
TEXT_TYPE = "Text Validation Type OR Show Slider Number"
TEXT_MIN = "Text Validation Min"
TEXT_MAX = "Text Validation Max"

# Header columns for mapping file.
DIMENSION = "dimension"
CONCEPT = "concept"
CATEGORIES = "categories"
STATISTIC = "statistic"
UNITS = "units"
RANGE = "range"

# Header columns for metadata.
DATASET_ID = "dataset_id"
TITLE = "title"
DESCRIPTION = "description"
PUBLISHER = "publisher"
ISSUED = "issued"
SUBJECT = "subject"
METADATA_HEADERS = [DATASET_ID, TITLE, DESCRIPTION, PUBLISHER, ISSUED, SUBJECT]

# Header columns for slices.
SLICE = "slice"
LABEL = "label"
LABEL_LANG = "label_lang"
COMMENT = "comment"
COMMENT_LANG = "comment_lang"

# Project specific configuration.
STUDY_ID = 'ncanda'


class Transformer(object):
    """Class that transforms a data dictionary into RDF.

    Transforms a data dictionary into the an RDF Data Cube Data Structure
    Definition graph.

    """
    def __init__(self):
        # clear internal data structures
        self._g = Graph()
        self._ns_dict = {}
        self._config_dict = {}
        self._add_prefixes()
        self._datadict = ""
        self._fields = []
        self._dimensions = []

    def query(self, query_object, processor='sparql', result='sparql',
              init_ns=None, init_bindings=None, use_store_provided=True,
              **kwargs):
        """
        Query this graph.

        Args:
            query_object (str): A SPARQL query.
            processor (str): Query processor to use.
            result (str): Result processor to use.
            init_ns (dict): A type of 'prepared queries' can be realised by
                providing initial variable bindings with init_bindings.
            init_bindings (dict): Initial namespaces are used to resolve
                prefixes used in the query, if none are given, the namespaces
                from the graph's namespace manager are used.
            use_store_provided (bool): Use the provided sparql store.
            **kwargs:

        Returns:
            An rdflib.query.QueryResult object.

        """
        return self._g.query(query_object, processor, result, init_ns,
                             init_bindings, use_store_provided, **kwargs)

    def build_graph(self, dd, mapping):
        """Constructs a graph from the data dictionary using a config file.

        Args:
            dd (str): Path to the data dictionary csv file.
            mapping (str): Path to a csv formatted config with supplementary
                information file.

        Returns:
            None

        """
        self._build_config_lookup(mapping)
        if dd is None:
            log("Data dictionary file not provided")
            return

        if not os.path.isfile(dd):
            log("{} file not found".format(dd))
            return
        log("Processing: {}".format(dd))

        # constants
        owl_class = self.ns.get("owl")["Class"]
        rdf_type = self.ns.get("rdf")["type"]
        rdf_property = self.ns.get("rdf")["Property"]
        dimension_property = self.ns.get("qb")["DimensionProperty"]
        measure_property = self.ns.get("qb")["MeasureProperty"]
        concept_rel = self.ns.get("qb")["concept"]
        rdfs_label = self.ns.get("rdfs")["label"]
        rdfs_subproperty_of = self.ns.get("rdfs")["subPropertyOf"]
        rdfs_subclass_of = self.ns.get("rdfs")["subClassOf"]
        rdfs_range = self.ns.get("rdfs")["range"]
        rdfs_see_also = self.ns.get("rdfs")["seeAlso"]
        unit_measure = self.ns.get("sibis")["unitMeasure"]
        statistic = self.ns.get("sibis")["statistic"]
        concept_scheme = self.ns.get("skos")["ConceptScheme"]
        concept = self.ns.get("skos")["Concept"]
        has_top_concept = self.ns.get("skos")["hasTopConcept"]
        top_concept_of = self.ns.get("skos")["topConceptOf"]
        in_scheme = self.ns.get("skos")["inScheme"]
        pref_label = self.ns.get("skos")["prefLabel"]
        notation = self.ns.get("skos")["notation"]

        self._datadict = os.path.basename(dd)
        with open(dd) as f:
            reader = csv.DictReader(f)
            for row in reader:
                field_name = row[FIELD_NAME]
                field_label = row[FIELD_LABEL]
                self._fields.append(field_name)
                node = self.ns.get("ncanda")[field_name]
                # Default to MeasureProperty.
                prop = measure_property
                # Use field_name to create "Field Name" label.
                if field_label:
                    label = field_label
                else:
                    split = [i.capitalize() for i in field_label.split('_')]
                    label = ' '.join(split)
                self._g.add((node, rdfs_label, Literal(label)))
                # Set prop for dimension properties.
                if (field_name in self._config_dict and
                        DIMENSION in self._config_dict[field_name]):
                    if self._config_dict[field_name][DIMENSION] == "y":
                        prop = dimension_property
                self._g.add((node, rdf_type, prop))
                self._g.add((node, rdf_type, rdf_property))
                # Annotate with Concepts.
                if (field_name in self._config_dict and
                        CONCEPT in self._config_dict[field_name]):
                    obj = URIRef(self._config_dict[field_name][CONCEPT])
                    self._g.add((node, concept_rel, obj))
                # Annotate with Range.
                if (field_name in self._config_dict and
                        RANGE in self._config_dict[field_name]):
                    xsd_type = URIRef(self._config_dict[field_name][RANGE])
                else:
                    xsd_type = self._data_element_type(row)
                self._g.add((node, rdfs_range, xsd_type))
                # Annotate with Units.
                if (field_name in self._config_dict and
                        UNITS in self._config_dict[field_name]):
                    obj = URIRef(self._config_dict[field_name][UNITS])
                    self._g.add((node, unit_measure, obj))
                # Annotate with Statistic.
                if (field_name in self._config_dict and
                        STATISTIC in self._config_dict[field_name]):
                    obj = URIRef(self._config_dict[field_name][STATISTIC])
                    self._g.add((node, statistic, obj))
                # Todo: Create qb:codeList for dimension and categorical data
                if (field_name in self._config_dict and
                        row[CHOICES]):
                    # Create a skos:Concept Class.
                    class_label = ''.join([i.capitalize()
                                          for i in field_name.split('_')])
                    class_uri = self.ns.get("ncanda")[class_label]
                    self._g.add((class_uri, rdf_type, owl_class))
                    self._g.add((class_uri, rdfs_subclass_of, concept))
                    title = "Code List Class for '{}' term."
                    self._g.add((class_uri,
                                 rdfs_label,
                                 Literal(title.format(
                                     field_label))))
                    # Create a skos:ConceptScheme.
                    scheme_label = "{}_concept_scheme".format(field_name)
                    concept_scheme_uri = self.ns.get("ncanda")[scheme_label]
                    self._g.add((concept_scheme_uri, rdf_type, concept_scheme))
                    self._g.add((concept_scheme_uri,
                                 notation,
                                 Literal(field_name)))
                    self._g.add((concept_scheme_uri,
                                 rdfs_label,
                                 Literal("Code List for '{}' term.".format(
                                     field_label))))
                    self._g.add((class_uri, rdfs_see_also, concept_scheme_uri))
                    choices = row[CHOICES].split("|")
                    # Create skos:Concept for each code.
                    for choice in choices:
                        k, v = choice.split(',')
                        code = k.strip()
                        code_label = v.strip()
                        choice_uri = self.ns.get("ncanda")['-'.join(
                            [field_name, code])]
                        self._g.add((choice_uri, rdf_type, concept))
                        self._g.add((choice_uri, rdf_type, class_uri))
                        self._g.add((choice_uri, notation, Literal(code)))
                        self._g.add((choice_uri,
                                     top_concept_of,
                                     concept_scheme_uri))
                        self._g.add((choice_uri,
                                     pref_label,
                                     Literal(code_label)))
                        self._g.add((concept_scheme_uri,
                                     has_top_concept,
                                     choice_uri))
                        self._g.add((concept_scheme_uri,
                                     in_scheme,
                                     choice_uri))

    def add_metadata(self, metadata_path):
        """Adds the dataset metadata to the graph

        Args:
            metadata_path (str): Path to a csv formatted file with the dataset
                metadata

        Returns:
            None

        """
        if metadata_path is None:
            log("Metadata file is not provided")
            return

        if not os.path.isfile(metadata_path):
            log("{} file not found".format(metadata_path))
            return
        log("Metadata processing: {}".format(metadata_path))

        # constants
        dataset = self.ns.get("qb")["DataSet"]
        title = self.ns.get("dct")["title"]
        description = self.ns.get("dct")["description"]
        publisher = self.ns.get("dct")["publisher"]
        issued = self.ns.get("dct")["issued"]
        subject = self.ns.get("dct")["subject"]

        with open(metadata_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                md_dataset_id = row[DATASET_ID]
                md_title = row[TITLE]
                md_description = row[DESCRIPTION]
                md_publisher = row[PUBLISHER]
                md_issued = row[ISSUED]
                md_subject = row[SUBJECT]

                term = URIRef(md_dataset_id)
                rdf_type = self.ns.get("rdf")["type"]
                self._g.add((term, rdf_type, dataset))
                self._g.add((term, title, Literal(md_title)))
                self._g.add((term, description, Literal(md_description)))
                self._g.add((term, publisher, Literal(md_publisher)))
                self._g.add((term, issued, Literal(md_issued,
                                                   datatype=XSD['date'])))
                self._g.add((term, subject, URIRef(md_subject)))

    def add_dsd(self, dimensions_csv, slices):
        """Adds data structure definition to the RDF graph.

        Args:
            dimensions_csv (str): CSV string of dimensions
            slices (str): Path to a csv formatted file with the slices
                metadata

        Returns:
            None

        """
        if self._datadict:
            dd = self.ns.get('sibis')[self._datadict]
        else:
            dd = URIRef(self._datadict)

        # read slices file
        slices_map = {}
        if os.path.isfile(slices):
            with open(slices) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    slicename = row[SLICE]
                    slices_map[slicename] = row

        # constants
        rdf_type = self.ns.get("rdf")["type"]
        dataset = self.ns.get("qb")["DataSet"]
        dsd = self.ns.get("qb")["DataStructureDefinition"]
        structure = self.ns.get("qb")["structure"]
        observation = self.ns.get("qb")["Observation"]
        qb_slice = self.ns.get("qb")["Slice"]
        component = self.ns.get("qb")["component"]
        component_attachment = self.ns.get("qb")["componentAttachment"]
        dimension = self.ns.get("qb")["dimension"]
        order = self.ns.get("qb")["order"]
        measure = self.ns.get("qb")["measure"]
        slice_key = self.ns.get("qb")["sliceKey"]
        slice_key_type = self.ns.get("qb")["SliceKey"]
        label = self.ns.get("rdfs")["label"]
        comment = self.ns.get("rdfs")["comment"]
        component_property = self.ns.get("qb")["componentProperty"]

        node = (dd, rdf_type, dsd)
        self._g.add(node)

        # Link to dataset.
        dataset_uri = list(self._g.subjects(rdf_type, dataset))
        if dataset_uri:
            self._g.add((dataset_uri[0], structure, dd))

        # Add dimension.
        index = 1
        # Check that dimensions were passed.
        if dimensions_csv:
            self._dimensions = dimensions_csv.split(",")
        slicename = ""
        for dim in self._dimensions:
            blank = BNode()
            self._g.add((dd, component, blank))
            self._g.add((blank, dimension, self.ns.get("ncanda")[dim]))
            self._g.add((blank, order, Literal(index)))
            if 1 == index:
                self._g.add((blank, component_attachment, observation))
            else:
                self._g.add((blank, component_attachment, qb_slice))
                slicename += self._dimensions[index - 1].title()
                slice_by = self.ns.get("ncanda")["sliceBy" + slicename]
                # Only add slices defined in csv inputs
                if slicename in slices_map:
                    self._g.add((dd, slice_key, slice_by))
                    md = slices_map[slicename]
                    if len(md[LABEL]) > 0:
                        label_literal = Literal(md[LABEL], lang=md[LABEL_LANG])
                        self._g.add((slice_by, label, label_literal))
                    if len(md[COMMENT]) > 0:
                        comment_literal = Literal(md[COMMENT],
                                                  lang=md[COMMENT_LANG])
                        self._g.add((slice_by, comment, comment_literal))
                    for slice_idx in range(1, index):
                        dim = self.ns.get("ncanda")[self._dimensions[slice_idx]]
                        self._g.add((slice_by, component_property, dim))
                        self._g.add((slice_by, rdf_type, slice_key_type))
            index += 1

        # Add measures.
        for field in self._fields:
            if field not in self._dimensions:
                blank = BNode()
                measure_field = self.ns.get("ncanda")[field]
                self._g.add((dd, component, blank))
                self._g.add((blank, measure, measure_field))

        # Add attributes.
        attribute = self.ns.get("qb")["attribute"]
        component_required = self.ns.get("qb")["componentRequired"]
        measure_property = self.ns.get("qb")["MeasureProperty"]
        unit_measure = self.ns.get("sibis")["unitMeasure"]
        blank = BNode()
        self._g.add((dd, component, blank))
        self._g.add((blank, attribute, unit_measure))
        self._g.add((blank, component_required, Literal("true",
                                                        datatype=XSD.boolean)))
        self._g.add((blank, component_attachment, measure_property))

    def add_observations(self, observations):
        """Adds a set of observations to the RDF graph

        Args:
            observations (str): Path to the observations csv file.
        Returns:
            None

        """
        if not os.path.isfile(observations):
            print("{} file not found".format(observations))
            return
        log("Processing: {}".format(observations))

        # constants
        if self._datadict:
            dd = self.ns.get('sibis')[self._datadict]
        else:
            dd = URIRef(self._datadict)
        rdf_type = self.ns.get("rdf")["type"]
        observation_type = self.ns.get("qb")["Observation"]
        observation = self.ns.get("qb")["observation"]
        slice = self.ns.get("qb")["Slice"]
        slice_structure = self.ns.get("qb")["sliceStructure"]
        dataset_type = self.ns.get("qb")["DataSet"]
        dataset_rel = self.ns.get("qb")["dataSet"]
        dataset_uriref = list(self._g.subjects(rdf_type, dataset_type))
        if dataset_uriref:
            dataset_uri = dataset_uriref[0]
        else:
            dataset_uri = URIRef("")

        with open(observations) as f:
            reader = csv.DictReader(f)
            index = 0
            for row in reader:
                obs = self._get_sha1_iri(row)
                slice_vals = [row.get(i) for i in self._dimensions[1:]]
                slice_iri = self._get_sha1_iri(slice_vals)
                self._g.add((obs, rdf_type, observation_type))
                self._g.add((obs, dataset_rel, dataset_uri))
                self._g.add((slice_iri, rdf_type, slice))
                self._g.add((slice_iri, slice_structure, dd))
                for key, vals in self._config_dict.iteritems():
                    field_name = vals[FIELD_NAME]
                    field_name_iri = self.ns.get("ncanda")[field_name]
                    # Only include the first dimension at the observation level.
                    if field_name not in self._dimensions[1:]:
                        self._g.add((obs, field_name_iri, Literal(row[key])))
                        self._g.add((slice_iri, observation, obs))
                    else:
                        # Add slice indices.
                        self._g.add((slice_iri,
                                     field_name_iri,
                                     Literal(row[key])))
                index += 1

    def display_graph(self):
        """Print the RDF file to stdout in turtle format.

        Returns:
            None

        """
        print(self._g.serialize(format='turtle'))

    def _add_prefix(self, prefix, namespace):
        ns = Namespace(namespace)
        self._g.bind(prefix, ns)
        self._ns_dict[prefix] = ns

    def _add_prefixes(self):
        self._add_prefix("ncanda", "http://ncanda.sri.com/terms#")
        self._add_prefix("fma", "http://purl.org/sig/fma#")
        self._add_prefix("prov", "http://w3c.org/ns/prov#")
        self._add_prefix("nidm", "http://purl.org/nidash/nidm#")
        self._add_prefix("fs", "http://www.incf.org/ns/nidash/fs#")
        self._add_prefix("qb", "http://purl.org/linked-data/cube#")
        self._add_prefix("sibis", "http://sibis.sri.com/terms#")
        self._add_prefix("iri", "http://sibis.sri.com/iri/")
        self._add_prefix("obo", "http://purl.obolibrary.org/obo/")

        # add in builtins
        self._add_prefix("owl", OWL)
        self._add_prefix("void", VOID)
        self._add_prefix("skos", SKOS)
        self._add_prefix("rdf", RDF)
        self._add_prefix("rdfs", RDFS)
        self._add_prefix("xsd", XSD)
        self._add_prefix("dct", DCTERMS)
        self._add_prefix("foaf", FOAF)

        # placeholder
        self._add_prefix("ph", "file:///placeholder#")

    @property
    def ns(self):
        return self._ns_dict

    def _data_element_type(self, row):
        # Get the data type uri from data element description.
        field_type = row.get(FIELD_TYPE)
        text_type = row.get(TEXT_TYPE)
        if field_type == 'text' and text_type == 'number':
            result = self.ns.get('xsd')['float']
        elif field_type == 'text' and text_type == 'integer':
            result = self.ns.get('xsd')['integer']
        elif field_type == 'radio' or field_type == 'dropdown':
            result = self._get_class_from_field_name(row.get(FIELD_NAME))
        elif text_type == 'calc':
            result = self.ns.get('xsd')['float']
        else:
            result = self.ns.get('xsd')['string']
        return result

    def _get_sha1_iri(self, row):
        # Get iri using based using sha1 of row.
        sha1 = hashlib.sha1(str(row)).hexdigest()
        return self.ns.get('iri')[sha1]

    def _get_class_from_field_name(self, field_name):
        # Create a skos:Concept Class.
        class_label = ''.join([i.capitalize()
                               for i in field_name.split('_')])
        return self.ns.get('ncanda')[class_label]

    def _build_config_lookup(self, config):
        if config is None:
            log("Mapping file not provided")
            return

        if not os.path.isfile(config):
            log("{} file not found".format(config))
            return

        with open(config) as f:
            reader = csv.DictReader(f)
            for row in reader:
                # drop empty values
                res = dict((k, v) for k, v in row.iteritems() if v is not "")
                self._config_dict[row[FIELD_NAME]] = res
