import pytest

from lamin_logger._map_synonyms import explode_aggregated_column_to_expand, map_synonyms


@pytest.fixture(scope="module")
def genes():
    import pandas as pd

    gene_symbols = ["A1CF", "A1BG", "FANCD1", "FANCD20"]

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
            "symbol": "PDCD1",
            "synonyms": "hSLE1|PD-1|PD1|SLEB2|CD279",
        },
        {
            "symbol": "PDCD1",
            "synonyms": "hSLE1|PD-1|PD1|SLEB2|CD279",
        },
    ]

    df = pd.DataFrame.from_records(records)

    return gene_symbols, df


def test_map_synonyms(genes):
    gene_symbols, df = genes

    mapping = map_synonyms(
        df=df, identifiers=gene_symbols, field="symbol", return_mapper=False
    )
    expected_synonym_mapping = ["A1CF", "A1BG", "BRCA2", "FANCD20"]
    assert mapping == expected_synonym_mapping


def test_map_synonyms_return_mapper(genes):
    gene_symbols, df = genes

    mapping = map_synonyms(
        df=df, identifiers=gene_symbols, field="symbol", return_mapper=True
    )

    expected_synonym_mapping = {"FANCD1": "BRCA2"}

    assert mapping == expected_synonym_mapping


def test_unsupported_field(genes):
    gene_symbols, df = genes
    with pytest.raises(KeyError):
        map_synonyms(df=df, identifiers=gene_symbols, field="name", return_mapper=False)


def test_explode_aggregated_column_to_expand(genes):
    _, df = genes
    with pytest.raises(AssertionError):
        explode_aggregated_column_to_expand(
            df=df, aggregated_col="synonyms", target_col="synonyms"
        )

    res = explode_aggregated_column_to_expand(
        df=df, aggregated_col="synonyms", target_col="symbol"
    )
    assert res.index.name == "synonyms"
    assert res.shape == (27, 1)
