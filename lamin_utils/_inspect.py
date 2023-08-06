from typing import Any, Dict, Iterable, List

from ._core import colors
from ._logger import logger
from ._map_synonyms import map_synonyms, to_str


def validate(
    identifiers: Iterable,
    field_values: Iterable,
    case_sensitive: bool = True,
    return_df: bool = False,
) -> Any:
    """Check if an iterable is in a list of values with case sensitive option."""
    import pandas as pd

    identifiers_idx = pd.Index(identifiers)
    identifiers_idx = to_str(identifiers_idx, case_sensitive=case_sensitive)

    field_values = to_str(field_values, case_sensitive=case_sensitive)

    # annotated what complies with the default ID
    matches = identifiers_idx.isin(field_values)
    if return_df:
        validated_df = pd.DataFrame(index=identifiers)
        validated_df["__validated__"] = matches
        return validated_df
    else:
        return matches


def inspect(
    df: Any,
    identifiers: Iterable,
    field: str,
    *,
    case_sensitive: bool = False,
    inspect_synonyms: bool = True,
    return_df: bool = False,
    logging: bool = True,
) -> Any:
    """Inspect if a list of identifiers are mappable to the entity reference.

    Args:
        identifiers: Identifiers that will be checked against the field.
        field: The BiontyField of the ontology to compare against.
                Examples are 'ontology_id' to map against the source ID
                or 'name' to map against the ontologies field names.
        return_df: Whether to return a Pandas DataFrame.

    Returns:
        - A Dictionary of "validated" and "not_validated" identifiers
        - If `return_df`: A DataFrame indexed by identifiers with a boolean
            `__validated__` column indicating compliance validation.
    """
    import pandas as pd

    def unique_rm_empty(idx: pd.Index):
        idx = idx.unique()
        return idx[(idx != "") & (~idx.isnull())]

    uniq_identifiers = unique_rm_empty(pd.Index(identifiers)).tolist()
    # empty DataFrame or input
    if df.shape[0] == 0 or len(uniq_identifiers) == 0:
        if return_df:
            return pd.DataFrame(index=identifiers, data={"__validated__": False})
        else:
            return {
                "validated": [],
                "not_validated": uniq_identifiers,
            }

    # check if index is compliant with exact matches
    validated_df = validate(
        identifiers=identifiers,
        field_values=df[field],
        case_sensitive=True,
        return_df=True,
    )

    # check without being case sensitive
    validated_df_noncs = validate(
        identifiers=identifiers,
        field_values=df[field],
        case_sensitive=False,
        return_df=True,
    )
    casing_warn_msg = ""
    if validated_df_noncs["__validated__"].sum() > validated_df["__validated__"].sum():
        casing_warn_msg = f"🟠 detected {colors.yellow('inconsistent casing')}"

    validated = unique_rm_empty(
        validated_df.index[validated_df["__validated__"]]
    ).tolist()
    unvalidated = unique_rm_empty(
        validated_df.index[~validated_df["__validated__"]]
    ).tolist()

    synonyms_warn_msg = ""
    if inspect_synonyms:
        try:
            synonyms_mapper = map_synonyms(
                df=df,
                identifiers=unvalidated,
                field=field,
                return_mapper=True,
                case_sensitive=False,
            )
            if len(synonyms_mapper) > 0:
                synonyms_warn_msg = f"🟠 detected {colors.yellow('synonyms')}"
        except Exception:
            pass

    n_unique_terms = len(validated) + len(unvalidated)
    n_empty = len(list(identifiers)) - n_unique_terms
    frac_unvalidated = round(len(unvalidated) / n_unique_terms * 100, 1)
    frac_validated = 100 - frac_unvalidated

    if logging:
        if n_empty > 0:
            logger.warning(
                f"received {n_unique_terms} unique terms, {n_empty} empty/duplicated"
                " terms are ignored"
            )
        logger.success(f"{len(validated)} terms ({frac_validated:.2f}%) are validated")
        if frac_validated < 100:
            warn_msg = (
                f"{len(unvalidated)} terms ({frac_unvalidated:.2f}%) are not validated"
            )
            hint = False
            if len(casing_warn_msg) > 0:
                warn_msg += f"\n   {casing_warn_msg}"
                hint = True
            if len(synonyms_warn_msg) > 0:
                warn_msg += f"\n   {synonyms_warn_msg}"
                hint = True
            if hint:
                warn_msg += (
                    "\n   to increase validated terms, standardize them via"
                    f" {colors.green('.map_synonyms()')}"
                )

            logger.warning(warn_msg)

    if return_df:
        return validated_df
    else:
        mapping: Dict[str, List[str]] = {}
        mapping["validated"] = validated
        mapping["not_validated"] = unvalidated
        return mapping
