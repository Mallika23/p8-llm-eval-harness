"""Maps the scorer names used in the dataset YAML to the scorer functions."""

from evals.scorers.deterministic import (
    allowed_values,
    exact_field_match,
    json_schema_valid,
    no_refusal,
)

SCORERS = {
    "json_schema_valid": json_schema_valid,
    "exact_field_match": exact_field_match,
    "allowed_values": allowed_values,
    "no_refusal": no_refusal,
}
