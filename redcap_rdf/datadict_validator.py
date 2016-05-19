""" Data Dictionary CSV Validator

@author: Victor Meyerson
"""

import os
import csv
import sys
import argparse

# Header columns for data dictionary
FIELD_NAME = "Variable / Field Name"
FORM = "Form Name"
FIELD_TYPE = "Field Type"
FIELD_LABEL = "Field Label"
CHOICES = "Choices, Calculations, OR Slider Labels"
TEXT_TYPE = "Text Validation Type OR Show Slider Number"
TEXT_MIN = "Text Validation Min"
TEXT_MAX = "Text Validation Max"
HEADERS = [FIELD_NAME, FORM, FIELD_TYPE, FIELD_LABEL, CHOICES, TEXT_TYPE,
           TEXT_MIN, TEXT_MAX]


class Validator(object):
    """Performs validation of a REDCap Data Dictionary.

    The validation outputs a summary of the missing information from a data
    dictionary that is recommended to complete for conversion to RDF.

    """
    def __init__(self):
        # clear internal data structures
        self._warnings = {}
        self._errors = {}
        self.verbose = False

    def process(self, dd, first_rows):
        """Runs the validation process.

        Args:
            dd (str): Path to the data dictionary.
            first_rows (list): Variable names that should start the dictionary
                (e.g. subject, arm, visit)

        Returns:
            None
        """
        if not os.path.isfile(dd):
            raise(IOError("{} file not found".format(dd)))

        if self.verbose:
            print("Processing: {}".format(dd))

        if first_rows and self.verbose:
            print("Running extra check for first rows")

        with open(dd) as f:
            reader = csv.DictReader(f)

            # check headers
            self._check_headers(reader.fieldnames)

            # check each row
            tmp_counter = 0
            for row in reader:
                self._check_row(row, reader.line_num)
                if tmp_counter < len(first_rows):
                    if row[FIELD_NAME] != first_rows[tmp_counter]:
                        message = "field should be '{}' found '{}'"
                        msg = message.format(first_rows[tmp_counter],
                                             row[FIELD_NAME])
                        self._append_error(row[FIELD_NAME], msg)
                    tmp_counter += 1
        if self.verbose:
            self._print_summary()

    def enable_verbose(self):
        """Sets Verbose printing to True.

        Returns:
            None
        """
        self.verbose = True

    @property
    def errors(self):
        """Get reported errors.

        Returns:
            A dict of errors.
        """
        return self._errors

    @property
    def warnings(self):
        """Get reported warnings.

        Returns:
            A dict of warnings.
        """
        return self._warnings

    # check functions
    def _check_headers(self, headers):
        for field in HEADERS:
            if field not in headers:
                msg = "Could not find: '{}' in the header".format(field)
                self._append_error("HEADERS", msg)

    def _check_row(self, row, number):
        message = "form: {}, field: {}, value type: {}, line: {}"
        if self.verbose:
            print(message.format(row[FORM], row[FIELD_NAME],
                                 row[FIELD_TYPE], number))
        self._check_label_exists(row)
        self._check_value_type(row)

    def _check_label_exists(self, row):
        label = row[FIELD_LABEL]
        if not label:
            msg = "No label is present."
            self._append_warning(row[FIELD_NAME], msg)

    def _check_value_type(self, row):
        if row[FIELD_TYPE] == "dropdown":
            self._validate_dropdown(row[FIELD_NAME], row[CHOICES])
        elif row[FIELD_TYPE] == "yesno":
            self._validate_yes_no(row[FIELD_NAME], row)
        elif row[FIELD_TYPE] == "text":
            self._validate_text(row[FIELD_NAME], row)
        else:
            val_type = row[FIELD_TYPE]
            msg = "Skipping validation of type: '{}'".format(val_type)
            self._append_warning(row[FIELD_NAME], msg)

    # validate various field type functions
    def _validate_dropdown(self, field, choices_str):
        choices = choices_str.split('|')
        if not choices[0]:
            msg = "There should be at least one choice."
            self._append_error(field, msg)
        for choice in choices:
            breakdown = choice.split(",")
            if len(breakdown) != 2:
                msg = "This is an invalid choice: {}".format(choice)
                self._append_error(field, msg)

    def _validate_yes_no(self, field, row):
        if len(row[CHOICES]) > 0:
            msg = "YesNo field should not have choices"
            self._append_error(field, msg)

    def _validate_text(self, field, row):
        if self.verbose:
            print("  Item: {} is a '{}'".format(row[FIELD_NAME],
                                                row[TEXT_TYPE]))
        if row[TEXT_TYPE] == "number":
            self._validate_numeric_range(field, row[TEXT_MIN], row[TEXT_MAX])
        else:
            msg = "No validation rules for type: '{}'".format(row[TEXT_TYPE])
            self._append_warning(field, msg)

    def _validate_numeric_range(self, field, low_str, high_str):
        if self.verbose:
            print("  Range: [{},{}]".format(low_str, high_str))
        if low_str:
            low = float(low_str)
        else:
            low = None
        if high_str:
            high = float(high_str)
        else:
            high = None
        if high < low:
            msg = "Max value ({}) should not be less than min value ({})"
            self._append_error(field, msg.format(high_str, low_str))
        elif not high:
            msg = "no maximum value set"
            self._append_warning(field, msg)
        elif not low:
            msg = "no minimum value set"
            self._append_warning(field, msg)
        else:
            msg = "no maximum or minimum value set"
            self._append_warning(field, msg)

    # accumulate messages
    def _append_error(self, key, msg):
        if key not in self._errors:
            self._errors[key] = [msg]
        else:
            self._errors[key].append(msg)

    def _append_warning(self, key, msg):
        if key not in self._warnings:
            self._warnings[key] = [msg]
        else:
            self._warnings[key].append(msg)

    # print helpers
    def _print_summary(self):
        print("SUMMARY")
        print("-------")
        message = "There are {} error(s)."
        print(message.format(len(self._errors)))
        self._print_details(self._errors)
        print("")
        message = "There are {} warning(s)."
        print(message.format(len(self._warnings)))
        self._print_details(self._warnings)

    def _print_details(self, ds):
        for (field, msgs) in ds.items():
            print("Field: '{}'".format(field))
            for msg in msgs:
                print("  {}".format(msg))


def csv_to_list(arg):
    return map(str, arg.split(','))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datadict",
                        help="The data dictionary csv file.",
                        required=True,
                        type=str)
    parser.add_argument("--first-rows",
                        help="Applies an extra check to the first rows.",
                        type=csv_to_list,
                        default=[])
    parser.add_argument("-v", "--verbose",
                        help="Increase output verbosity.",
                        action="store_true")
    args = parser.parse_args()
    validator = Validator()
    if args.verbose:
        validator.enable_verbose()
    validator.process(args.datadict, args.first_rows)


if __name__ == "__main__":
    sys.exit(main())
