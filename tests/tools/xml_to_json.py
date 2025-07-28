#!/usr/bin/env python3

import xmltodict
import json
import sys
from collections import OrderedDict

if len(sys.argv) != 3:
    print("Usage: xml_to_json.py <input.xml> <output.json>")
    sys.exit(1)

input_xml, output_json = sys.argv[1], sys.argv[2]

with open(input_xml, 'r') as f:
    xml_content = f.read()
xml_dict = xmltodict.parse(xml_content, dict_constructor=OrderedDict)

with open(output_json, 'w') as f:
    json.dump(xml_dict, f, indent=2, sort_keys=True)
