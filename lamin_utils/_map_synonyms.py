from typing import Any, Dict, Iterable, List, Literal, Union

from ._logger import logger


def map_synonyms(
    df: Any,
    identifiers: Iterable,
    field: str,
    *,
    case_sensitive: bool = False,
    return_mapper: bool = False,
    mute: bool = False,
    synonyms_field: str = "synonyms",
    sep: str = "|",
    keep: Literal["first", "last", False] = "first",
) -> Union[Dict[str, str], List[str]]:
    """Maps input identifiers against a concatenated synonyms column.

    Will also standardize casing.

    Args:
        df: Reference DataFrame.
        identifiers: Identifiers that will be mapped against a field.
        return_mapper: If True, returns {input synonyms : standardized field name}.
        case_sensitive: Whether the mapping is case sensitive.
        keep : {'first', 'last', False}, default 'first'
            When a synonym maps to multiple standardized values, determines
            which duplicates to mark as `pandas.DataFrame.duplicated`
            - "first": returns the first mapped standardized value
            - "last": returns the last mapped standardized value
            - False: returns all mapped standardized value
        synonyms_field: The field representing the concatenated synonyms.
        synonyms_sep: Which separator is used to separate synonyms.
        field: The field representing the identifiers.

    Returns:
        - If return_mapper is False: a list of mapped field values.
        - If return_mapper is True: a dictionary of mapped values with mappable
            identifiers as keys and values mapped to field as values.
    """
    import pandas as pd

    identifiers = list(identifiers)

    # empty DataFrame or input
    n_input = len(identifiers)
    if df.shape[0] == 0 or n_input == 0:
        if return_mapper:
            return {}
        else:
            return identifiers

    if field not in df.columns:
        raise KeyError(
            f"field '{field}' is invalid! Available fields are: {list(df.columns)}"
        )
    if synonyms_field not in df.columns:
        raise KeyError(
            f"synonyms_field '{synonyms_field}' is invalid! Available fields"
            f" are: {list(df.columns)}"
        )
    if field == synonyms_field:
        raise KeyError("synonyms_field must be different from field!")

    # A DataFrame indexed by the passed identifiers
    mapped_df = pd.DataFrame(data={"orig_ids": identifiers})
    mapped_df["__agg__"] = to_str(mapped_df["orig_ids"], case_sensitive=case_sensitive)

    # __agg__ is a column of identifiers based on case_sensitive
    df["__agg__"] = to_str(df[field], case_sensitive=case_sensitive)
    # field_map is {"__agg__": field_value} for mappable values
    field_map = pd.merge(mapped_df, df, on="__agg__").set_index("__agg__")[field]

    # only runs if synonyms mapping is needed
    # unique of field_map is needed here due to possible multiple matches of identifier
    if len(field_map.unique()) < mapped_df.shape[0]:
        # {synonym: name}
        syn_map = explode_aggregated_column_to_map(
            df=df,
            agg_col=synonyms_field,
            target_col=field,
            keep=keep,
            sep=sep,
        )

        if not case_sensitive:
            # convert the synonyms to the same case_sensitive
            syn_map.index = syn_map.index.str.lower()
            # TODO: allow returning duplicated entries
            syn_map = syn_map[syn_map.index.drop_duplicates()]
        # if values are already in field_map, do not apply synonyms mapping
        syn_map = {
            k: v for k, v in syn_map.to_dict().items() if k not in field_map.index
        }
    else:
        syn_map = {}

    # mapped synonyms will have values, otherwise NAs
    mapped_df.index = mapped_df["orig_ids"]
    mapped = mapped_df["__agg__"].map({**field_map.to_dict(), **syn_map})

    n_mapped = (~mapped.isna()).sum()
    if n_mapped > 0 and not mute:
        logger.info(f"standardized {n_mapped}/{n_input} terms")

    if return_mapper:
        # only returns mapped synonyms
        mapper = mapped[~mapped.isna()].to_dict()
        mapper = {k: v for k, v in mapper.items() if k != v}
        if keep is False:
            logger.warning(
                "returning mapper might contain lists as values when 'keep=False'"
            )
            return {k: v[0] if len(v) == 1 else v for k, v in mapper.items()}
        else:
            return mapper
    else:
        # returns a list in the input order with synonyms replaced
        mapped_list = mapped.fillna(mapped_df["orig_ids"]).tolist()
        if keep is False:
            logger.warning("returning list might contain lists when 'keep=False'")
            return [
                v[0] if isinstance(v, list) and len(v) == 1 else v for v in mapped_list
            ]
        else:
            return mapped_list


def to_str(identifiers: Any, case_sensitive: bool = False):
    """Convert a pandas series values to strings with case sensitive option."""
    if identifiers.dtype.name == "category":
        try:
            categorical = identifiers.cat
        except AttributeError:
            categorical = identifiers
        if "" not in categorical.categories:
            values = categorical.add_categories("")
        else:
            values = identifiers
        values = values.fillna("").astype(str)
    else:
        values = identifiers.fillna("")
    if case_sensitive is False:
        values = values.str.lower()
    return values


def not_empty_none_na(values: Iterable):
    """Return values that are not empty string, None or NA."""
    import pandas as pd

    if not isinstance(values, (pd.Series, pd.Index)):
        values = pd.Series(values)

    return values[pd.Series(values).fillna("").astype(bool)]


def explode_aggregated_column_to_map(
    df,
    agg_col: str,
    target_col=str,
    keep: Literal["first", "last", False] = "first",
    sep: str = "|",
):
    """Explode values from an aggregated DataFrame column to map to a target column.

    Args:
        df: A DataFrame containing the agg_col and target_col.
        agg_col: The name of the aggregated column
        target_col: the name of the target column
                    If None, use the index as the target column
        keep : {'first', 'last', False}, default 'first'
            Determines which duplicates to mark as `pandas.DataFrame.duplicated`
        sep: Splits all values of the agg_col by this separator.

    Returns:
        a pandas.Series index by the split values from the aggregated column
    """
    df = df[[target_col, agg_col]].drop_duplicates().dropna(subset=[agg_col])

    # subset to df with only non-empty strings in the agg_col
    df = df.loc[not_empty_none_na(df[agg_col]).index]

    df[agg_col] = df[agg_col].str.split(sep)
    df_explode = df.explode(agg_col)
    # remove rows with same values in agg_col and target_col
    df_explode = df_explode[df_explode[agg_col] != df_explode[target_col]]

    # group by the agg_col and return based on keep for the target_col values
    gb = df_explode.groupby(agg_col)[target_col]
    if keep == "first":
        return gb.first()
    elif keep == "last":
        return gb.last()
    elif keep is False:
        return gb.apply(list)
