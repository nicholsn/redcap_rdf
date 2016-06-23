##
##  See COPYING file distributed along with the redcap_rdf package for the
##  copyright and license terms
##
""" Data Dictionary Transformer to RDF Data Cube.
"""
import os
import csv
import hashlib

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, FOAF, RDF, RDFS, OWL, SKOS, VOID, XSD

from redcap_rdf.util import log, AttrDict, get_dict_reader

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
PROJECT = 'ncanda'
LANG = 'en'


class Transformer(object):
    """Class that transforms a data dictionary into RDF.

    Transforms a data dictionary into the an RDF Data Cube Data Structure
    Definition graph.

    """

    def __init__(self):
        # clear internal data structures
        self._g = Graph()
        self._ns_dict = {}
        self._terms_dict = {}
        self._config_dict = {}
        self._add_prefixes()
        self._add_terms()
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
        log("Processing: {}".format(dd))

        # self._build_config_lookup(mapping)

        self._build_datadict(dd)

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
                self._g.add((term,
                             self.terms.rdf_type,
                             self.terms.dataset_type))
                self._g.add((term,
                             self.terms.title,
                             Literal(md_title)))
                self._g.add((term,
                             self.terms.description,
                             Literal(md_description)))
                self._g.add((term,
                             self.terms.publisher,
                             Literal(md_publisher)))
                self._g.add((term,
                             self.terms.issued,
                             Literal(md_issued,
                                     datatype=XSD['date'])))
                self._g.add((term,
                             self.terms.subject,
                             URIRef(md_subject)))

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
            dd_iri = self.ns.get(PROJECT)[self._datadict]
        else:
            dd_iri = URIRef(self._datadict)

        node = (dd_iri, self.terms.rdf_type, self.terms.dsd_type)
        self._g.add(node)

        # Link to dataset.
        dataset_uri = list(self._g.subjects(self.terms.rdf_type,
                                            self.terms.dataset_type))
        if dataset_uri:
            self._g.add((dataset_uri[0], self.terms.structure, dd_iri))

        # Add dimension.
        index = 1
        # Check that dimensions were passed.
        if dimensions_csv:
            self._dimensions = dimensions_csv.split(",")
        # Create the slice key iri.
        slice_by_iri = self._get_slice_by_iri()
        self._g.add((slice_by_iri,
                     self.terms.rdf_type,
                     self.terms.slice_key_type))
        for dim in self._dimensions:
            blank = BNode()
            self._g.add((dd_iri, self.terms.component, blank))
            self._g.add((blank,
                         self.terms.dimension,
                         self.ns.get(PROJECT)[dim]))
            self._g.add((blank, self.terms.order, Literal(index)))
            # First dimension attached to the observation level.
            if 1 == index:
                self._g.add((blank,
                             self.terms.component_attachment,
                             self.terms.observation_type))
            # Remaining dimensions added in order to the slice level.
            else:
                self._g.add((blank,
                             self.terms.component_attachment,
                             self.terms.slice_type))
                # Add slice key to data structure.
                self._g.add((dd_iri, self.terms.slice_key, slice_by_iri))
                # Add label to slice key.
                label_literal = self._get_slice_label()
                self._g.add((slice_by_iri,
                             self.terms.rdfs_label,
                             label_literal))
                # Add comment to slice key.
                comment_literal = self._get_slice_comment()
                self._g.add((slice_by_iri,
                             self.terms.rdfs_comment,
                             comment_literal))

                for slice_idx in range(1, index):
                    dim = self.ns.get(PROJECT)[self._dimensions[slice_idx]]
                    self._g.add((slice_by_iri,
                                 self.terms.component_property,
                                 dim))
            index += 1

        # Add measures.
        for field in self._fields:
            if field not in self._dimensions:
                blank = BNode()
                measure_field = self.ns.get(PROJECT)[field]
                self._g.add((dd_iri, self.terms.component, blank))
                self._g.add((blank, self.terms.measure, measure_field))

        # Add attributes.
        blank = BNode()
        self._g.add((dd_iri, self.terms.component, blank))
        self._g.add((blank, self.terms.attribute, self.terms.unit_measure))
        self._g.add((blank,
                     self.terms.component_required,
                     Literal("true", datatype=XSD.boolean)))
        self._g.add((blank,
                     self.terms.component_attachment,
                     self.terms.measure_property_type))

    def add_observations(self, observations):
        """Adds a set of observations to the RDF graph

        Args:
            observations (str): Path to the observations csv file.
        Returns:
            None

        """
        log("Processing: {}".format(observations))

        # Constants.
        if self._datadict:
            dd = self.ns.get(PROJECT)[self._datadict]
        else:
            dd = URIRef(self._datadict)
        dataset_iri = self._get_dataset_iri()
        reader = get_dict_reader(observations)
        index = 0
        for row in reader:
            obs = self._get_sha1_iri(row)
            slice_vals = [row.get(i) for i in self._dimensions[1:]]
            slice_iri = self._get_sha1_iri(slice_vals)
            self._g.add((obs,
                         self.terms.rdf_type,
                         self.terms.observation_type))
            self._g.add((obs, self.terms.dataset, dataset_iri))
            self._g.add((slice_iri,
                         self.terms.rdf_type,
                         self.terms.slice_type))
            self._g.add((dataset_iri, self.terms.slice, slice_iri))
            self._g.add((slice_iri, self.terms.slice_structure, dd))
            for field_name, value in row.iteritems():
                if field_name.endswith('_label'):
                    continue
                field_name_iri = self.ns.get(PROJECT)[field_name]
                # Get the rdfs:range to determine datatype.
                rdfs_ranges = list(self._g.objects(
                    field_name_iri, self.terms.rdfs_range))
                if rdfs_ranges:
                    rdfs_range_iri = rdfs_ranges[0]
                else:
                    error = "rdfs:range not set for {}.".format(field_name_iri)
                    log(error)
                    raise(KeyError(error))
                # Only include the first dimension at the observation level.
                if field_name not in self._dimensions[1:]:
                    # If the range is not an XSD Literal (i.e., this is an
                    # object property), use coded iri.
                    xsd = str(XSD[''].defrag())
                    if str(rdfs_range_iri.defrag()) != xsd:
                        coded_iri = self._convert_literal_to_coded_iri(
                            rdfs_range_iri, value)
                        self._g.add((obs,
                                     field_name_iri,
                                     coded_iri))
                    else:
                        datatype_iri = rdfs_range_iri
                        self._g.add((obs,
                                     field_name_iri,
                                     Literal(value,
                                             datatype=datatype_iri)))
                    self._g.add((slice_iri, self.terms.observation, obs))
                else:
                    # Add slice indices.
                    coded_iri = self._convert_literal_to_coded_iri(
                        rdfs_range_iri, value)
                    self._g.add((slice_iri, field_name_iri, coded_iri))
            index += 1

    def display_graph(self):
        """Print the RDF file to stdout in turtle format.

        Returns:
            None

        """
        print(self._g.serialize(format='turtle'))

    def _convert_literal_to_coded_iri(self, rdfs_range_iri, literal):
        # Given a range and coded literal, returns a iri representing the
        # literal
        coded_iris = list(self._g.subjects(self.terms.rdf_type,
                                           rdfs_range_iri))
        result = RDF['nil']
        for coded_iri in coded_iris:
            notations = list(self._g.objects(coded_iri, self.terms.notation))
            notation = notations[0]
            if literal == str(notation):
                result = coded_iri
        return result

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
        """
        Get information from registered namespaces.

        Returns:
            A dictionary that returns an rdflib.URIRef.

        """
        return self._ns_dict

    def _get_slice_label(self):
        # Use dimension to create a slice key label.
        label = "slice by {0} "
        return Literal(label.format(self._dimensions[0]),
                       lang=LANG)

    def _get_slice_comment(self):
        # Use dimensions to create a slice key comment.
        slices = ', '.join(self._dimensions[1:])
        label = "Slice by grouping {0} together, fixing values for {1}."
        return Literal(label.format(self._dimensions[0], slices),
                       lang=LANG)

    def _add_terms(self):
        result = AttrDict(
            # NIDM properties.
            unit_measure=self.ns.get("sibis")["unitMeasure"],
            statistic=self.ns.get("sibis")["statistic"],

            # Builtin classes.
            owl_class=self.ns.get("owl")["Class"],
            property_type=self.ns.get("rdf")["Property"],

            # Builtin properties.
            rdf_type=self.ns.get("rdf")["type"],
            rdfs_comment=self.ns.get("rdfs")["comment"],
            rdfs_label=self.ns.get("rdfs")["label"],
            rdfs_subclass_of=self.ns.get("rdfs")["subClassOf"],
            rdfs_range=self.ns.get("rdfs")["range"],
            rdfs_see_also=self.ns.get("rdfs")["seeAlso"],
            rdfs_subproperty_of=self.ns.get("rdfs")["subPropertyOf"],

            # Data cube classes.
            observation_type=self.ns.get("qb")["Observation"],
            slice_type=self.ns.get("qb")["Slice"],
            dataset_type=self.ns.get("qb")["DataSet"],
            dsd_type=self.ns.get("qb")["DataStructureDefinition"],
            slice_key_type=self.ns.get("qb")["SliceKey"],
            dimension_property_type=self.ns.get("qb")["DimensionProperty"],
            measure_property_type=self.ns.get("qb")["MeasureProperty"],
            coded_property_type=self.ns.get("qb")["CodedProperty"],

            # Data cube properties.
            slice_structure=self.ns.get("qb")["sliceStructure"],
            observation=self.ns.get("qb")["observation"],
            dataset=self.ns.get("qb")["dataSet"],
            attribute=self.ns.get("qb")["attribute"],
            component_required=self.ns.get("qb")["componentRequired"],
            structure=self.ns.get("qb")["structure"],
            component=self.ns.get("qb")["component"],
            component_attachment=self.ns.get("qb")["componentAttachment"],
            dimension=self.ns.get("qb")["dimension"],
            order=self.ns.get("qb")["order"],
            measure=self.ns.get("qb")["measure"],
            slice_key=self.ns.get("qb")["sliceKey"],
            slice=self.ns.get("qb")["slice"],
            component_property=self.ns.get("qb")["componentProperty"],
            concept=self.ns.get("qb")["concept"],
            code_list=self.ns.get("qb")["codeList"],

            # DC Terms properties.
            title=self.ns.get("dct")["title"],
            description=self.ns.get("dct")["description"],
            publisher=self.ns.get("dct")["publisher"],
            issued=self.ns.get("dct")["issued"],
            subject=self.ns.get("dct")["subject"],

            # SKOS classes.
            concept_scheme_type=self.ns.get("skos")["ConceptScheme"],
            concept_type=self.ns.get("skos")["Concept"],

            # SKOS properties.
            has_top_concept=self.ns.get("skos")["hasTopConcept"],
            top_concept_of=self.ns.get("skos")["topConceptOf"],
            in_scheme=self.ns.get("skos")["inScheme"],
            pref_label=self.ns.get("skos")["prefLabel"],
            notation=self.ns.get("skos")["notation"]
        )
        self._terms_dict = result

    @property
    def terms(self):
        return self._terms_dict

    def _data_element_type(self, row):
        # Get the data type uri from data element description.
        field_type = row.get(FIELD_TYPE)
        text_type = row.get(TEXT_TYPE)
        if field_type == 'text' and text_type == 'number':
            result = self.ns.get('xsd')['float']
        elif field_type == 'text' and text_type == 'integer':
            result = self.ns.get('xsd')['integer']
        elif field_type in ['dropdown', 'radio', 'yesno']:
            result = self._get_class_from_field_name(row.get(FIELD_NAME))
        elif field_type == 'calc':
            result = self.ns.get('xsd')['float']
        else:
            result = self.ns.get('xsd')['string']
        return result

    def _get_slice_by_iri(self):
        # Constructs an IRI for a slice definition.
        slice_by = 'sliceBy'
        for dim in self._dimensions[1:]:
            dim_parts = dim.split('_')
            slice_by += ''.join([i.title() for i in dim_parts])
        return self.ns.get(PROJECT)[slice_by]

    def _get_sha1_iri(self, row):
        # Get iri using based using sha1 of row.
        sha1 = hashlib.sha1(str(row)).hexdigest()
        return self.ns.get('iri')[sha1]

    def _get_class_from_field_name(self, field_name):
        # Create a skos:Concept Class.
        class_label = ''.join([i.capitalize()
                               for i in field_name.split('_')])
        return self.ns.get(PROJECT)[class_label]

    def _build_datadict(self, dd):
        self._datadict = os.path.basename(dd)
        reader = get_dict_reader(dd)
        for row in reader:
            field_name = row[FIELD_NAME]
            field_label = row[FIELD_LABEL]
            self._fields.append(field_name)
            subject_iri = self.ns.get(PROJECT)[field_name]
            # Set predicate type to qb:MeasureProperty and rdf:Property.
            self._g.add((subject_iri,
                         self.terms.rdf_type,
                         self.terms.measure_property_type))
            self._g.add((subject_iri,
                         self.terms.rdf_type,
                         self.terms.property_type))
            # Set predicate rdfs:label.
            if field_label:
                label = field_label
            else:
                split = [i.capitalize() for i in field_name.split('_')]
                label = ' '.join(split)
            self._g.add((subject_iri, self.terms.rdfs_label, Literal(label)))
            # Generate a skow:Concept in project namespace.
            concept_type = self._get_class_from_field_name(field_name)
            self._g.add((subject_iri, self.terms.concept, concept_type))
            # Annotate with Range.
            xsd_type = self._data_element_type(row)
            self._g.add((subject_iri, self.terms.rdfs_range, xsd_type))
            if row[CHOICES] and row[FIELD_TYPE] != 'calc':
                # Create a skos:Concept Class.
                class_label = ''.join([i.capitalize()
                                       for i in field_name.split('_')])
                class_uri = self.ns.get(PROJECT)[class_label]
                self._g.add((class_uri,
                             self.terms.rdf_type,
                             self.terms.owl_class))
                self._g.add((class_uri,
                             self.terms.rdfs_subclass_of,
                             self.terms.concept_type))
                title = "Code List Class for '{}' term."
                self._g.add((class_uri,
                             self.terms.rdfs_label,
                             Literal(title.format(
                                 field_label.strip()))))
                # Create a skos:ConceptScheme.
                scheme_label = "{}ConceptScheme".format(class_label)
                concept_scheme_uri = self.ns.get(PROJECT)[scheme_label]
                self._g.add((concept_scheme_uri,
                             self.terms.rdf_type,
                             self.terms.concept_scheme_type))
                self._g.add((concept_scheme_uri,
                             self.terms.notation,
                             Literal(field_name)))
                self._g.add((concept_scheme_uri,
                             self.terms.rdfs_label,
                             Literal("Code List for '{}' term.".format(
                                 field_label.strip()))))
                self._g.add((class_uri,
                             self.terms.rdfs_see_also,
                             concept_scheme_uri))
                # Annotate with code list
                self._g.add((subject_iri,
                             self.terms.code_list,
                             concept_scheme_uri))
                choices = row[CHOICES].split("|")
                # Create skos:Concept for each code.
                for choice in choices:
                    k, v = choice.split(',')
                    code = k.strip()
                    code_label = v.strip()
                    code_split = '-'.join(code.lower().split('_'))
                    field_name_split = '-'.join(field_name.split('_'))
                    choice_uri = self.ns.get(PROJECT)['-'.join(
                        [field_name_split, code_split])]
                    self._g.add((choice_uri,
                                 self.terms.rdf_type,
                                 self.terms.concept_type))
                    self._g.add((choice_uri,
                                 self.terms.rdf_type,
                                 class_uri))
                    self._g.add((choice_uri,
                                 self.terms.notation,
                                 Literal(code)))
                    self._g.add((choice_uri,
                                 self.terms.top_concept_of,
                                 concept_scheme_uri))
                    self._g.add((choice_uri,
                                 self.terms.pref_label,
                                 Literal(code_label)))
                    self._g.add((concept_scheme_uri,
                                 self.terms.has_top_concept,
                                 choice_uri))

    def _build_config_lookup(self, config):
        reader = get_dict_reader(config)
        for row in reader:
            # drop empty values
            res = dict((k, v) for k, v in row.iteritems() if v is not "")
            self._config_dict[row[FIELD_NAME]] = res

    def _add_dimension_type(self, subject_iri):
        # Set types for dimension properties.
        self._g.add((subject_iri,
                     self.terms.rdf_type,
                     self.terms.dimension_property_type))
        self._g.add((subject_iri,
                     self.terms.rdf_type,
                     self.terms.coded_property_type))

    def _get_dataset_iri(self):
        # Get an IRI for the dataset
        dataset_uriref = list(self._g.subjects(self.terms.rdf_type,
                                               self.terms.dataset_type))
        if dataset_uriref:
            dataset_iri = dataset_uriref[0]
        else:
            dataset_iri = URIRef("")
        return dataset_iri
