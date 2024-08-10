#!env/bin/python3
# -*- coding: utf-8 -*-

import os
import json
import argparse
from pydantic import BaseModel, TypeAdapter, ValidationError, Field, EmailStr, AnyUrl, UUID4, Json
from pydantic.networks import HttpUrl, IPvAnyAddress, AnyHttpUrl
from datetime import datetime, date, time, timedelta
from typing import List


def check_file_type(file):
    base, ext = os.path.splitext(file)
    if ext.lower() != ".json":
        raise argparse.ArgumentTypeError(f"File '{file}' is not a JSON file")
    return file

types_to_check = [
    (datetime, "date-time"),
    (time, "time"),
    (date, "date"),
    (timedelta, "duration"),
    (EmailStr, "email"),
    (AnyUrl, "uri"),
    (AnyHttpUrl, "uri-reference"),
    (UUID4, "uuid"),
    (Json, "json-pointer"),
]

class Converter:
    def __init__(self, input_file, quiet=False):
        self.quiet = quiet
        self.json_data = {}
        self.schema = {
            "$schema": "http://json-schema.org/draft/2020-12/schema",
            "$id": "",
            "title": "",
            "description": "",
        }
        self.conversion_table = {
            str: "string",
            int: "integer",
            float: "number",
            dict: "object",
            list: "array",
            bool: "boolean",
            type(None): "null"
        }

        # Check if the input file exists
        if not os.path.exists(input_file):
            raise Exception(f"File '{input_file}' not found")

        # Read the input file
        with open(input_file, "r") as f:
            self.json_data = json.load(f)

    # Get the format of a string
    # Built-in formats: date-time, time, date, duration, email, idn-email, hostname, idn-hostname, ipv4, ipv6, uuid, uri, uri-reference, iri, iri-reference, regex, uri-template, json-pointer, relative-json-pointer, regex
    def get_format(self, _value):
        for type_to_check, result in types_to_check:
            try:
                TypeAdapter(type_to_check).validate_python(_value)
                return result
            except ValidationError:
                pass
        return None

    def get_type_obj(self, value) -> dict:
        data = {
            "type":""
        }

        # Check type
        if type(value) not in self.conversion_table:
            raise Exception(f"Type '{type(value)}' not supported")
        data["type"] = self.conversion_table[type(value)]

        # Further checks
        if data["type"] == "string":
            format = self.get_format(value)
            if format:
                data["format"] = format
        elif data["type"] == "object":
            data = self.dict_to_jsonschema(value)
        elif data["type"] == "array":
            # Check if the array is empty
            if len(value):
                data["items"] = self.get_type_obj(value[0])
        return data

    def dict_to_jsonschema(self, _dict):
        obj={
            "type": "object",
            "properties": {},
        }
        for key, value in _dict.items():
            obj["properties"][key] = self.get_type_obj(value)
        return obj

    def convert(self):
        # Get the type of the data
        obj = self.get_type_obj(self.json_data)
        self.schema.update(obj)

        # Ask the user for the schema $id, title, and description
        if not self.quiet:
            if not self.schema["$id"]:
                self.schema["$id"] = input("Enter the schema $id: ")
            if not self.schema["title"]:
                self.schema["title"] = input("Enter the schema title: ")
            if not self.schema["description"]:
                self.schema["description"] = input("Enter the schema description: ")

        # Save the schema to a file
        with open("schema.json", "w") as f:
            json.dump(self.schema, f, indent=4)
        print("schema saved to 'schema.json'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert to JSON Schema")
    parser.add_argument("-i", "--input", help="Input file", type=check_file_type, required=True)
    parser.add_argument("-q", "--quiet", help="Quiet mode", action="store_true")

    args = parser.parse_args()
    converter = Converter(args.input, args.quiet)
    converter.convert()
