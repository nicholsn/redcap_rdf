""" Data Dictionary CSV Validator

@author: Victor Meyerson
"""

import os
import csv
import sys
import argparse


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

# TODO: make these fields more flexible for other validations
FIXED_ROWS = ["subject", "arm", "visit"]


def check_headers(headers):
    ret_val = False
    for field in HEADERS:
        if field not in headers:
            print "Could not find: %s in the header" % field
            ret_val = True
    return ret_val


def check_row(row, number):
    print "form: %s, field: %s, value type: %s" % (row[FORM],
                                                   row[FIELD_NAME],
                                                   row[FIELD_TYPE])
    check_value_type(row)


def check_value_type(row):
    if row[FIELD_TYPE] == "dropdown":
        return validate_dropdown(row[CHOICES])
    elif row[FIELD_TYPE] == "yesno":
        return validate_yes_no(row)
    elif row[FIELD_TYPE] == "text":
        return validate_text(row)
    else:
        print "WARNING: Skipping validation of type: '%s'" % row[FIELD_TYPE]


def validate_dropdown(choicesStr):
    ret_val = False
    choices = choicesStr.split('|')
    if len(choices) <= 1:
        print "There should be more than one choice"
    for choice in choices:
        breakdown = choice.split(",")
        if len(breakdown) != 2:
            print "This is an invalid choice: %s" % choice
            ret_val = True
    return ret_val


def validate_yes_no(row):
    ret_val = False
    if len(row[CHOICES]) > 0:
        print "YesNo field should not have choices"
        ret_val = True
    return ret_val


def validate_text(row):
    ret_val = False
    print "  Item: %s is a %s" % (row[FIELD_NAME], row[TEXT_TYPE])
    if row[TEXT_TYPE] == "number":
        ret_val = validate_numeric_range(row[TEXT_MIN], row[TEXT_MAX])
    else:
        ret_val = True
        print "  No validation rules for type: '%s'" % row[TEXT_TYPE]
    return ret_val


def validate_numeric_range(low_str, high_str):
    ret_val = False
    print "  Range: [%s,%s]" % (low_str, high_str)
    low = float(low_str)
    if high_str != "":
        high = float(high_str)
        if high < low:
            ret_val = True
            print "  Max value (%s) should not be less than min value (%s)" % \
                  (high_str, low_str)
    else:
        print "WARNING: no maximum value set"
    return ret_val


def process(dd, fixed_rows):
    if not os.path.isfile(dd):
        print "%s file not found" % dd
        return
    print "Processing: %s" % dd

    if fixed_rows:
        print "Running extra check for first rows"

    with open(dd) as f:
        reader = csv.DictReader(f)
        # check existance of headers
        if check_headers(reader.fieldnames):
            print "ERROR: Header check FAILED!"
            return
        # check each row
        tmp_val = False
        tmp_counter = 0
        for row in reader:
            tmp_Val = check_row(row, reader.line_num) or tmp_val
            if fixed_rows and tmp_counter < len(FIXED_ROWS):
                if row[FIELD_NAME] != FIXED_ROWS[tmp_counter]:
                    print "ERROR: field should be '%s' found '%s'" % \
                          (FIXED_ROWS[tmp_counter], row[FIELD_NAME])
                    tmp_val = True
                tmp_counter += 1
        if tmp_val:
            print "ERROR: There was a failure in at least one row"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datadict",
                        help="the data dictionary csv file",
                        type=str)
    parser.add_argument("--fixed-rows",
                        help="applies an extra check to the first rows",
                        action="store_true")
    parser.add_argument("-v", "--verbose",
                        help="increase output verbosity",
                        action="store_true")
    args = parser.parse_args()
    process(args.datadict, args.fixed_rows)


if __name__ == "__main__":
    sys.exit(main())
