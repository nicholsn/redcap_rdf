##
##  See COPYING file distributed along with the redcap_rdf package for the
##  copyright and license terms
##
""" Data Dictionary Transformer to Semantic

@author: Victor Meyerson
"""
import os
import csv

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, FOAF, RDF, RDFS, OWL, SKOS, VOID, XSD

# Header columns for data dictionary
FIELD_NAME = "Variable / Field Name"
FORM = "Form Name"
FIELD_TYPE = "Field Type"
FIELD_LABEL = "Field Label"
CHOICES = "Choices, Calculations, OR Slider Labels"
TEXT_TYPE = "Text Validation Type OR Show Slider Number"
TEXT_MIN = "Text Validation Min"
TEXT_MAX = "Text Validation Max"

# Header columns for mapping file
DIMENSION = "dimension"
CONCEPT = "concept"
CATEGORIES = "categories"
STATISTIC = "statistic"
UNITS = "units"

# Header columns for metadata
DATASET_ID = "dataset_id"
TITLE = "title"
DESCRIPTION = "description"
PUBLISHER = "publisher"
ISSUED = "issued"
SUBJECT = "subject"
METADATA_HEADERS = [DATASET_ID, TITLE, DESCRIPTION, PUBLISHER, ISSUED, SUBJECT]

# Header columns for slices
SLICE = "slice"
LABEL = "label"
LABEL_LANG = "label_lang"
COMMENT = "comment"
COMMENT_LANG = "comment_lang"


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

    def build_graph(self, dd, config):
        """Constructs a graph from the data dictionary using a config file.

        Args:
            dd (str): Path to the data dictionary csv file.
            config (str): Path to a csv formatted config with supplementary
                information file.

        Returns:
            None

        """
        self._build_config_lookup(config)
        if not os.path.isfile(dd):
            print("{} file not found".format(dd))
            return
        print("Processing: {}".format(dd))

        # constants
        rdf_property = self._get_ns("rdf")["Property"]
        dimension_property = self._get_ns("qb")["DimensionProperty"]
        measure_property = self._get_ns("qb")["MeasureProperty"]
        concept = self._get_ns("qb")["concept"]
        rdfs_label = self._get_ns("rdfs")["label"]
        rdfs_subPropertyOf = self._get_ns("rdfs")["subPropertyOf"]
        rdfs_range = self._get_ns("rdfs")["range"]

        self._datadict = os.path.basename(dd)
        with open(dd) as f:
            reader = csv.DictReader(f)
            for row in reader:
                field_name = row[FIELD_NAME]
                self._fields.append(field_name)
                # TODO: Use Field Label if available else field_name.split('_')
                # and capitalize and join with a space.
                node = self._get_ns("ncanda")[field_name]
                self._g.add((node, rdfs_label, Literal(field_name)))
                prop = measure_property
                if (field_name in self._config_dict and
                        DIMENSION in self._config_dict[field_name]):
                    if self._config_dict[field_name][DIMENSION] == "y":
                        prop = dimension_property
                self._g.add((node, rdf_property, prop))
                if (field_name in self._config_dict and
                        CONCEPT in self._config_dict[field_name]):
                    obj = URIRef(self._config_dict[field_name][CONCEPT])
                    self._g.add((node, concept, obj))
                if (field_name in self._config_dict and
                        UNITS in self._config_dict[field_name]):
                    obj = self._get_term(self._config_dict[field_name][UNITS])
                    self._g.add((node, rdfs_range, obj))

    def add_metadata(self, metadata_path):
        """Adds the dataset metadata to the graph

        Args:
            metadata_path (str): Path to a csv formatted file with the dataset
                metadata

        Returns:
            None

        """
        if not os.path.isfile(metadata_path):
            print("{} file not found".format(metadata_path))
            return
        print("Metadata processing: {}".format(metadata_path))

        # constants
        dataset = self._get_ns("qb")["DataSet"]
        title = self._get_ns("dct")["title"]
        description = self._get_ns("dct")["description"]
        publisher = self._get_ns("dct")["publisher"]
        issued = self._get_ns("dct")["issued"]
        subject = self._get_ns("dct")["subject"]

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
                rdf_type = self._get_ns("rdf")["type"]
                self._g.add((term, rdf_type, dataset))
                self._g.add((term, title, Literal(md_title)))
                self._g.add((term, description, Literal(md_description)))
                self._g.add((term, publisher, Literal(md_publisher)))
                self._g.add((term, issued, Literal(md_issued, datatype=XSD.date)))
                self._g.add((term, subject, URIRef(md_subject)))

    def add_dsd(self, dimensions_csv, slices):
        """Adds data structure definition to the RDF graph

        Args:
            dimensions_csv (str): CSV string of dimensions
            slices (str): Path to a csv formatted file with the slices
                metadata

        Returns:
            None

        """
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
        rdf_type = self._get_ns("rdf")["type"]
        dsd = self._get_ns("qb")["DataStructureDefinition"]
        observation = self._get_ns("qb")["Observation"]
        qb_slice = self._get_ns("qb")["Slice"]
        component = self._get_ns("qb")["component"]
        component_attachment = self._get_ns("qb")["componentAttachment"]
        dimension = self._get_ns("qb")["dimension"]
        order = self._get_ns("qb")["order"]
        measure = self._get_ns("qb")["measure"]
        slice_key = self._get_ns("qb")["sliceKey"]
        label = self._get_ns("rdfs")["label"]
        comment = self._get_ns("rdfs")["comment"]
        component_property = self._get_ns("qb")["componentProperty"]

        node = (dd, rdf_type, dsd)
        self._g.add(node)

        # add dimension
        index = 1
        # check that dimensions were passed
        if 0 < len(dimensions_csv):
            dimensions = dimensions_csv.split(",")
        else:
            dimensions = []
        slicename = ""
        for dim in dimensions:
            blank = BNode()
            self._g.add((dd, component, blank))
            self._g.add((blank, dimension, URIRef(dim)))
            self._g.add((blank, order, Literal(index)))
            if 1 == index:
                self._g.add((blank, component_attachment, observation))
            else:
                self._g.add((blank, component_attachment, qb_slice))
                slicename += dimensions[index - 1].title()
                slice_by = self._get_ns("sibis")["sliceBy" + slicename]
                self._g.add((dd, slice_key, slice_by))
                if slicename in slices_map:
                    md = slices_map[slicename]
                    if len(md[LABEL]) > 0:
                        label_literal = Literal(md[LABEL], lang=md[LABEL_LANG])
                        self._g.add((slice_by, label, label_literal))
                    if len(md[COMMENT]) > 0:
                        comment_literal = Literal(md[COMMENT], lang=md[COMMENT_LANG])
                        self._g.add((slice_by, comment, comment_literal))
                for slice_idx in range(1, index):
                    self._g.add((slice_by, component_property, URIRef(dimensions[slice_idx])))
            index = index + 1

        # add measures
        for field in self._fields:
            if field not in dimensions:
                blank = BNode()
                self._g.add((dd, component, blank))
                self._g.add((blank, measure, URIRef(field)))

        # add attributes
        attribute = self._get_ns("qb")["attribute"]
        component_required = self._get_ns("qb")["componentRequired"]
        measure_property = self._get_ns("qb")["MeasureProperty"]
        unit_measure = self._get_ns("sibis")["unitMeasure"]
        blank = BNode()
        self._g.add((dd, component, blank))
        self._g.add((blank, attribute, unit_measure))
        self._g.add((blank, component_required, Literal("true", datatype=XSD.boolean)))
        self._g.add((blank, component_attachment, measure_property))

    def display_graph(self):
        """Print the RDF file to stdout in turtle format.

        Returns:
            None

        """
        print(self._g.serialize(format='n3'))

    def _add_prefix(self, prefix, namespace):
        ns = Namespace(namespace)
        self._g.bind(prefix, ns)
        self._ns_dict[prefix] = ns

    def _add_prefixes(self):
        self._add_prefix("ncanda", "http://ncanda.sri.com/terms.ttl#")
        self._add_prefix("fma", "http://purl.org/sig/fma#")
        self._add_prefix("prov", "http://w3c.org/ns/prov#")
        self._add_prefix("nidm", "http://purl.org/nidash/nidm#")
        self._add_prefix("fs", "http://www.incf.org/ns/nidash/fs#")
        self._add_prefix("qb", "http://purl.org/linked-data/cube#")
        self._add_prefix("sibis", "http://sibis.sri.com/terms#")

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

    def _get_ns(self, prefix):
        if prefix in self._ns_dict:
            return self._ns_dict[prefix]
        return None

    def _get_term(self, term):
        parts = term.split(":")
        ns = parts[0]
        resource = parts[1]
        return self._get_ns(ns)[resource]

    def _build_config_lookup(self, config):
        if not os.path.isfile(config):
            print("{} file not found".format(config))
            return

        with open(config) as f:
            reader = csv.DictReader(f)
            for row in reader:
                # drop empty values
                res = dict((k, v) for k, v in row.iteritems() if v is not "")
                self._config_dict[row[FIELD_NAME]] = res

    # 'private' member data
    _g = Graph()
    _ns_dict = {}
    _config_dict = {}
    _datadict = ""
    _fields = []
