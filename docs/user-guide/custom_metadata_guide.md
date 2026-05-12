# Custom Metadata Fields Guide

TOSTADAS's metadata validation can be extended with a JSON configuration file that defines per-field checks and transformations for non-standard BioSample packages or lab-specific column naming conventions.

---

## When to use this

Use custom metadata fields when:
- Your BioSample package has required fields not in the default `Pathogen.cl.1.0` template
- Your source Excel files use different column names than NCBI expects
- You want empty cells automatically filled with a default value like `"Not Provided"`

---

## JSON file format

```json
{
    "your_column_name": {
        "type": "string",
        "samples": "All",
        "replace_empty_with": "Not Provided",
        "new_field_name": "ncbi_expected_name"
    },
    "another_column": {
        "type": "integer",
        "samples": ["FL0001", "FL0002"],
        "replace_empty_with": "",
        "new_field_name": ""
    }
}
```

A working example is at `assets/custom_meta_fields/example_custom_fields.json`.

### Field properties

| Key | Description | Accepted values |
|---|---|---|
| `type` | Expected data type — TOSTADAS will attempt to cast values that don't match | `string`, `integer`, `float`, `boolean` |
| `samples` | Which samples to apply this check to | `"All"`, `["All"]`, or a list of sample names |
| `replace_empty_with` | Fill empty cells with this value | Any string, number, or `""` to skip |
| `new_field_name` | Rename this column before submission | New column name string, or `""` to keep the original |

All four keys are optional — omit any you don't need.

---

## How to run

```bash
nextflow run main.nf \
  -profile <...> \
  --validate_custom_fields \
  --custom_fields_file path/to/my_fields.json \
  ...
```

Both parameters are required together. `--validate_custom_fields` without a `--custom_fields_file` has no effect.

---

## Outputs

After validation, check `validation_outputs/errors/custom_fields_error.txt` for a per-field and per-sample log:

```
collection_site:
    Found 'All' in samples list — checking all samples
    
FL0001:
    collection_site was empty. Replaced with "Not Provided"
    Renamed column 'collection_site' to 'geo_loc_name'

FL0002:
    All custom field checks passed
```

---

## Type casting rules

When a value's type doesn't match the declared `type`, TOSTADAS attempts a Python-native cast:

| From → To | Behavior |
|---|---|
| int → bool | `0` → `False`, non-zero → `True` |
| float → bool | `0.0` → `False`, non-zero → `True` |
| bool → int | `True` → `1`, `False` → `0` |
| float → int | Truncates (4.8 → 4, not rounded) |
| any → string | Uses literal value: `True` → `"True"`, `0` → `"0"` |
| string → int | Requires a whole-number string; `"8.0"` fails |
| string → float | `"8"` → `8.0` (appends `.0`) |

---

## Behavior rules

- A field is skipped if its key in the JSON is an empty string
- If a listed sample name doesn't exist in the metadata, it's skipped and logged
- If `"All"` appears anywhere in the `samples` list, all samples are checked regardless of other entries
- An empty `samples` list defaults to checking all samples

---

## Built-in profiles with pre-configured custom fields

Two TOSTADAS profiles include a custom fields JSON configured for their BioSample package:

| Profile | Package | Custom fields JSON |
|---|---|---|
| `nwss` | `SARS-CoV-2.wwsurv.1.0` | `assets/custom_meta_fields/nwss_custom_fields.json` |
| `pulsenet` | `OneHealthEnteric.1.0` | `assets/custom_meta_fields/onehealth_custom_fields.json` |

These are applied automatically when you use the profile — you don't need `--custom_fields_file` unless you want to override them.
