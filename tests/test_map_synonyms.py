import pandas as pd
import pytest

from lamin_utils._map_synonyms import (
    explode_aggregated_column_to_map,
    map_synonyms,
    not_empty_none_na,
    to_str,
)


@pytest.fixture(scope="module")
def genes():
    gene_symbols = ["A1CF", "A1BG", "FANCD1", "FANCD20", "GCS"]

    records = [
        {
            "symbol": "BRCA1",
            "synonyms": "PPP1R53|RNF53|FANCS|BRCC1",
        },
        {
            "symbol": "A1BG",
            "synonyms": "",
        },
        {
            "symbol": "BRCA2",
            "synonyms": "FAD|FAD1|BRCC2|FANCD1|FACD|FANCD|XRCC11",
        },
        {
            "symbol": "A1CF",
            "synonyms": "ACF|ACF64|APOBEC1CF|ACF65|ASP",
        },
        {
            "symbol": "GCLC",
            "synonyms": "GCS|BRCA1",
        },
        {
            "symbol": "UGCG",
            "synonyms": "GCS",
        },
    ]

    df = pd.DataFrame.from_records(records)

    return gene_symbols, df


def test_map_synonyms(genes):
    gene_symbols, df = genes

    mapping = map_synonyms(df=df, identifiers=gene_symbols, field="symbol")
    assert mapping == ["A1CF", "A1BG", "BRCA2", "FANCD20", "GCLC"]

    # no synonyms
    mapping = map_synonyms(df=df, identifiers=["BRCA1", "A1BG"], field="symbol")
    assert mapping == ["BRCA1", "A1BG"]


def test_map_synonyms_field_synonym(genes):
    _, df = genes

    mapping = map_synonyms(df=df, identifiers=["BRCA1", "BRCC1"], field="symbol")
    assert mapping == ["BRCA1", "BRCA1"]


def test_map_synonyms_return_mapper(genes):
    gene_symbols, df = genes

    mapper = map_synonyms(
        df=df, identifiers=gene_symbols, field="symbol", return_mapper=True
    )

    assert mapper == {"FANCD1": "BRCA2", "GCS": "GCLC"}


def test_map_synonyms_case_sensitive(genes):
    _, df = genes

    mapping = map_synonyms(
        df=df, identifiers=["A1CF", "FANCD1", "a1CF", "fancd1"], field="symbol"
    )
    assert mapping == ["A1CF", "BRCA2", "A1CF", "BRCA2"]

    mapping = map_synonyms(
        df=df,
        identifiers=["A1CF", "FANCD1", "a1CF", "fancd1"],
        field="symbol",
        case_sensitive=True,
    )
    assert mapping == ["A1CF", "BRCA2", "a1CF", "fancd1"]


def test_map_synonyms_empty_values(genes):
    _, df = genes

    result = map_synonyms(
        df=df,
        identifiers=["", " ", None, "CD3", "FANCD1"],
        field="symbol",
        return_mapper=False,
    )
    assert result == ["", " ", None, "CD3", "BRCA2"]

    mapper = map_synonyms(
        df=df,
        identifiers=["", " ", None, "CD3", "FANCD1"],
        field="symbol",
        return_mapper=True,
    )
    assert mapper == {"FANCD1": "BRCA2"}


def test_map_synonyms_keep(genes):
    _, df = genes

    assert map_synonyms(
        df, identifiers=["GCS", "A1CF"], field="symbol", keep=False
    ) == [["GCLC", "UGCG"], "A1CF"]

    assert map_synonyms(
        df, identifiers=["GCS", "A1CF"], field="symbol", keep=False, return_mapper=True
    ) == {"GCS": ["GCLC", "UGCG"]}


def test_map_synonyms_unsupported_field(genes):
    gene_symbols, df = genes
    with pytest.raises(KeyError):
        map_synonyms(df=df, identifiers=gene_symbols, field="name", return_mapper=False)
    with pytest.raises(KeyError):
        map_synonyms(
            df=df,
            identifiers=gene_symbols,
            field="symbol",
            synonyms_field="name",
            return_mapper=False,
        )
    with pytest.raises(KeyError):
        map_synonyms(
            df=df,
            identifiers=gene_symbols,
            field="symbol",
            synonyms_field="symbol",
            return_mapper=False,
        )


def test_map_synonyms_empty_df():
    assert (
        map_synonyms(
            df=pd.DataFrame(), identifiers=[], field="name", return_mapper=True
        )
        == {}
    )
    assert map_synonyms(df=pd.DataFrame(), identifiers=[], field="name") == []


def test_to_str():
    import numpy as np

    assert to_str(pd.Index(["A", "a", None, np.nan])).tolist() == ["a", "a", "", ""]
    assert to_str(pd.Series(["A", "a", None, np.nan])).tolist() == ["a", "a", "", ""]
    assert to_str(
        pd.Series(["A", "a", None, np.nan]), case_sensitive=True
    ).tolist() == ["A", "a", "", ""]


def test_not_empty_none_na():
    import numpy as np

    assert not_empty_none_na(["a", None, "", np.nan]).loc[0] == "a"
    assert not_empty_none_na(pd.Index(["a", None, "", np.nan])).tolist() == ["a"]
    assert not_empty_none_na(
        pd.Series(["a", None, "", np.nan], index=["1", "2", "3", "4"])
    ).to_dict() == {"1": "a"}


def test_explode_aggregated_column_to_map(genes):
    _, df = genes
    assert explode_aggregated_column_to_map(
        df, agg_col="synonyms", target_col="symbol"
    ).to_dict() == {
        "ACF": "A1CF",
        "ACF64": "A1CF",
        "ACF65": "A1CF",
        "APOBEC1CF": "A1CF",
        "ASP": "A1CF",
        "BRCA1": "GCLC",
        "BRCC1": "BRCA1",
        "BRCC2": "BRCA2",
        "FACD": "BRCA2",
        "FAD": "BRCA2",
        "FAD1": "BRCA2",
        "FANCD": "BRCA2",
        "FANCD1": "BRCA2",
        "FANCS": "BRCA1",
        "GCS": "GCLC",
        "PPP1R53": "BRCA1",
        "RNF53": "BRCA1",
        "XRCC11": "BRCA2",
    }

    assert (
        explode_aggregated_column_to_map(
            df, agg_col="synonyms", target_col="symbol", keep="last"
        ).get("GCS")
        == "UGCG"
    )
    assert explode_aggregated_column_to_map(
        df, agg_col="synonyms", target_col="symbol", keep=False
    ).get("GCS") == ["GCLC", "UGCG"]


def test_to_str_categorical_series():
    import numpy as np

    df = pd.DataFrame([np.nan, None, "a"])
    df[0] = df[0].astype("category")

    assert to_str(df[0]).tolist() == ["", "", "a"]
