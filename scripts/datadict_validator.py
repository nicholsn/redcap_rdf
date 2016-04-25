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


def checkHeaders(headers):
    retVal = False
    for field in HEADERS:
        if field not in headers:
            print "Could not find: %s in the header" % field
            retVal = True
    return retVal


def checkRow(row, number):
    print "form: %s, field: %s, value type: %s" % (row[FORM],
                                                   row[FIELD_NAME],
                                                   row[FIELD_TYPE])
    checkValueType(row)


def checkValueType(row):
    if row[FIELD_TYPE] == "dropdown":
        return validateDropdown(row[CHOICES])
    elif row[FIELD_TYPE] == "yesno":
        return validateYesNo(row)
    elif row[FIELD_TYPE] == "text":
        return validateText(row)
    else:
        print "WARNING: Skipping validation of type: '%s'" % row[FIELD_TYPE]


def validateDropdown(choicesStr):
    retVal = False
    choices = choicesStr.split('|')
    if len(choices) <= 1:
        print "There should be more than one choice"
    for choice in choices:
        breakdown = choice.split(",")
        if len(breakdown) != 2:
            print "This is an invalid choice: %s" % choice
            retVal = True
    return retVal


def validateYesNo(row):
    retVal = False
    if len(row[CHOICES]) > 0:
        print "YesNo field should not have choices"
        retVal = True
    return retVal


def validateText(row):
    retVal = False
    print "  Item: %s is a %s" % (row[FIELD_NAME], row[TEXT_TYPE])
    if row[TEXT_TYPE] == "number":
        retVal = validateNumericRange(row[TEXT_MIN], row[TEXT_MAX])
    else:
        retVal = True
        print "  No validation rules for type: '%s'" % row[TEXT_TYPE]
    return retVal


def validateNumericRange(lowStr, highStr):
    retVal = False
    print "  Range: [%s,%s]" % (lowStr, highStr)
    low = float(lowStr)
    if highStr != "":
        high = float(highStr)
        if high < low:
            retVal = True
            print "  Max value (%s) should not be less than min value (%s)" % \
                  (highStr, lowStr)
    else:
        print "WARNING: no maximum value set"
    return retVal


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
        if checkHeaders(reader.fieldnames):
            print "ERROR: Header check FAILED!"
            return
        # check each row
        tmpVal = False
        tmpCounter = 0
        for row in reader:
            tmpVal = checkRow(row, reader.line_num) or tmpVal
            if fixed_rows and tmpCounter < len(FIXED_ROWS):
                if row[FIELD_NAME] != FIXED_ROWS[tmpCounter]:
                    print "ERROR: field should be '%s' found '%s'" % \
                          (FIXED_ROWS[tmpCounter], row[FIELD_NAME])
                    tmpVal = True
                tmpCounter += 1
        if tmpVal:
            print "ERROR: There was a failure in at least one row"


def main(argv):
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
    main(sys.argv)
