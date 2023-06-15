from typing import Any, Dict, Iterable, List, Union


def map_synonyms(
    df: Any,
    identifiers: Iterable,
    field: str,
    *,
    synonyms_field: str = "synonyms",
    sep: str = "|",
    return_mapper: bool = False,
) -> Union[Dict[str, str], List[str]]:
    """Maps input identifiers against a concatenated synonyms column.

    Args:
        identifiers: Identifiers that will be mapped against an field.
        field: The field representing the identifiers.
        return_mapper: If True, returns {identifiers : <mapped field values>}.

    Returns:
        - A list of mapped field values if return_mapper is False.
        - A dictionary of mapped values with mappable identifiers as keys
            and values mapped to field as values if return_mapper is True.
    """
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

    alias_map = explode_aggregated_column_to_expand(
        df,
        aggregated_col=synonyms_field,
        target_col=field,
        sep=sep,
    )[field]

    if return_mapper:
        mapped_dict = {
            item: alias_map.get(item)
            for item in identifiers
            if alias_map.get(item) is not None and alias_map.get(item) != item
        }
        return mapped_dict
    else:
        mapped_list = [alias_map.get(item, item) for item in identifiers]
        return mapped_list


def explode_aggregated_column_to_expand(
    df: Any,
    aggregated_col: str,
    target_col=None,
    sep: str = "|",
) -> Any:
    """Explode values from an aggregated DataFrame column to expand a target column.

    Args:
        df: A DataFrame containing the aggregated_col and target_col.
        aggregated_col: The name of the aggregated column
        target_col: the name of the target column
                    If None, use the index as the target column
        sep: Splits all values of the aggregated_col by this separator.

    Returns:
        a DataFrame index by the split values from the aggregated column;
        the target column is aggregated so that the new index is unique.
    """
    import pandas as pd

    if target_col is None:
        # take the index as the target column
        if df.index.name is None:
            target_col = df.index.name = "index"
        else:
            target_col = df.index.name
    if aggregated_col == target_col:
        raise AssertionError("synonyms and target column can't be the same!")
    try:
        df = df.reset_index()[[aggregated_col, target_col]].copy()
    except KeyError:
        raise KeyError(f"{aggregated_col} field is not found!")

    # explode the values from the aggregated cells into new rows
    df[aggregated_col] = df[aggregated_col].str.split(sep)
    exploded_df = df.explode(aggregated_col)

    # if any values in the aggregated column is already in the target col
    # sets those values of the aggregated column to None
    exploded_df.loc[
        exploded_df[aggregated_col].isin(exploded_df[target_col]), aggregated_col
    ] = None

    # set the values aggregated_col equal the target_col if None before concat
    exploded_df[aggregated_col] = exploded_df[aggregated_col].fillna(
        exploded_df[target_col]
    )

    # append the additional values in the target column to the df
    add_values = exploded_df[
        ~exploded_df[target_col].isin(exploded_df[aggregated_col])
    ][target_col].unique()
    add_df = pd.DataFrame(data={target_col: add_values, aggregated_col: add_values})

    # aggregate the target column so that the new index (aggregated column) is unique
    df_concat = pd.concat([exploded_df, add_df])
    df_concat = df_concat.astype(str)
    df_concat = df_concat.groupby(aggregated_col).agg(sep.join)

    return df_concat
