from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from lamin_utils import logger

if TYPE_CHECKING:
    import pandas as pd


def search(
    df: pd.DataFrame,
    string: str,
    field: str = "name",
    limit: int | None = 20,
    synonyms_field: str | None = "synonyms",
    case_sensitive: bool = False,
    synonyms_sep: str = "|",
    keep: Literal["first", "last", False] = "first",
) -> pd.DataFrame:
    """Search a given string against a field.

    Args:
        df: The DataFrame to search in.
        string: The input string to match against the field values.
        field: The name of the field to search against.
        limit: The maximum number of top results to return. If None, returns all results.
        synonyms_field: The name of the field containing synonyms.
            If None, no synonym matching is performed.
        case_sensitive: Whether the match should be case sensitive. Defaults to False.
        synonyms_sep: The separator used in the synonyms field.
        keep: Determines which duplicates to keep when grouping results.
            Options are "first", "last", or False (keep all).

    Returns:
        A DataFrame of ranked search results.
        This DataFrame contains the matched rows from the input DataFrame,
        sorted by the match ratio in descending order.
        It includes all columns from the input DataFrame plus an additional '__ratio__' column indicating the match score.

    Raises:
        KeyError: If the specified field or synonyms_field is not found in the DataFrame.
        ValueError: If an invalid value is provided for the 'keep' parameter.
    """
    import pandas as pd

    from ._map_synonyms import explode_aggregated_column_to_map

    def _fuzz(
        string: str,
        iterable: pd.Series,
        case_sensitive: bool = True,
        limit: int | None = None,
    ):
        from rapidfuzz import fuzz, process, utils

        # use WRatio to account for typos
        if " " in string:
            scorer = fuzz.QRatio
        else:
            scorer = fuzz.WRatio

        processor = None if case_sensitive else utils.default_process
        results = process.extract(
            string,
            iterable,
            scorer=scorer,
            limit=limit,
            processor=processor,
        )
        try:
            return pd.DataFrame(results).set_index(2)[1]
        except KeyError:
            # no search results
            return None

    # empty DataFrame
    if df.shape[0] == 0:
        return df

    # search against each of the synonyms
    if (synonyms_field in df.columns) and (synonyms_field != field):
        # creates field_value:synonym
        mapper = explode_aggregated_column_to_map(
            df,
            agg_col=synonyms_field,  # type:ignore
            target_col=field,
            keep=keep,
            sep=synonyms_sep,
        )
        if keep is False:
            mapper = mapper.explode()
        # adds field_value:field_value to field_value:synonym
        df_field = pd.Series(df[field].values, index=df[field], name=field)
        df_field.index.name = synonyms_field
        df_field = df_field[df_field.index.difference(mapper.index)]
        mapper = pd.concat([mapper, df_field])
        df_exp = mapper.reset_index()
        target_column = synonyms_field
    else:
        if synonyms_field == field:
            logger.warning(
                "Input field is the same as synonyms field, skipping synonyms matching"
            )
        df_exp = df[[field]].copy()
        target_column = field

    # add matching scores as a __ratio__ column
    ratios = _fuzz(
        string=string,
        iterable=df_exp[target_column],
        case_sensitive=case_sensitive,
        limit=limit,
    )
    if ratios is None:
        return pd.DataFrame(columns=df.columns)
    df_exp["__ratio__"] = ratios

    if limit is not None:
        df_exp = df_exp[~df_exp["__ratio__"].isna()]
    # only keep the max score between field and synonyms for each entry
    # here groupby is also used to remove duplicates of field values
    df_exp_grouped = df_exp.groupby(field).max("__ratio__")
    # subset to original field values (as synonyms were mixed in before)
    df_exp_grouped = df_exp_grouped[df_exp_grouped.index.isin(df[field])]
    df_scored = df.set_index(field).loc[df_exp_grouped.index]
    df_scored["__ratio__"] = df_exp_grouped["__ratio__"]

    return df_scored.sort_values("__ratio__", ascending=False)
