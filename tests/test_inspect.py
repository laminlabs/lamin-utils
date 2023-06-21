import pandas as pd
import pytest

from lamin_logger._inspect import inspect


@pytest.fixture(scope="module")
def genes():
    data = {
        "gene symbol": ["A1CF", "A1BG", "FANCD1", "corrupted"],
        "hgnc id": ["HGNC:24086", "HGNC:5", "HGNC:1101", "corrupted"],
        "ensembl_gene_id": [
            "ENSG00000148584",
            "ENSG00000121410",
            "ENSG00000188389",
            "ENSG0000corrupted",
        ],
    }
    data = pd.DataFrame(data).set_index("ensembl_gene_id")

    records = [
        {
            "symbol": "A1BG",
            "hgnc id": "HGNC:5",
            "ensembl_gene_id": "ENSG00000121410",
            "synonyms": "",
        },
        {
            "symbol": "BRCA2",
            "hgnc id": "HGNC:1101",
            "ensembl_gene_id": "ENSG00000188389",
            "synonyms": "FAD|FAD1|BRCC2|FANCD1|FACD|FANCD|XRCC11",
        },
        {
            "symbol": "A1CF",
            "hgnc id": "HGNC:24086",
            "ensembl_gene_id": "ENSG00000148584",
            "synonyms": "ACF|ACF64|APOBEC1CF|ACF65|ASP",
        },
    ]
    df = pd.DataFrame.from_records(records)

    return df, data


def test_inspect_iterable(genes):
    df, data = genes

    mapping = inspect(df=df, identifiers=data.index, field="ensembl_gene_id")
    assert mapping == {
        "mapped": ["ENSG00000148584", "ENSG00000121410", "ENSG00000188389"],
        "not_mapped": ["ENSG0000corrupted"],
    }

    mapping = inspect(df=df, identifiers=data["hgnc id"], field="hgnc_id")
    assert mapping == {
        "mapped": ["HGNC:24086", "HGNC:5", "HGNC:1101"],
        "unmapped": ["corrupted"],
    }


def test_inspect_return_df(genes):
    df, data = genes

    mapping = inspect(
        df=df, identifiers=data.index, field="ensembl_gene_id", return_df=True
    )

    expected_df = pd.DataFrame(
        index=[
            "ENSG00000148584",
            "ENSG00000121410",
            "ENSG00000188389",
            "ENSG0000corrupted",
        ],
        data={
            "__mapped__": [True, True, True, False],
        },
    )

    assert mapping.equals(expected_df)


def test_inspect_case_sensitive(genes):
    df, _ = genes

    mapping = inspect(df=df, identifiers=["A1CF", "A1BG", "a1cf"], field="symbol")
    assert mapping == {"mapped": ["A1CF", "A1BG", "a1cf"], "not_mapped": []}

    mapping = inspect(
        df=df, identifiers=["A1CF", "A1BG", "a1cf"], field="symbol", case_sensitive=True
    )
    assert mapping == {"mapped": ["A1CF", "A1BG"], "not_mapped": ["a1cf"]}
