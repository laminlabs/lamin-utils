import pandas as pd
import pytest
from lamin_utils._search import search


@pytest.fixture(scope="module")
def df():
    records = [
        {
            "ontology_id": "CL:0000084",
            "name": "T cell",
            "synonyms": "T-cell|T lymphocyte|T-lymphocyte",
            "children": ["CL:0000798", "CL:0002420", "CL:0002419", "CL:0000789"],
        },
        {
            "ontology_id": "CL:0000236",
            "name": "B cell",
            "synonyms": "B lymphocyte|B-lymphocyte|B-cell",
            "children": ["CL:0009114", "CL:0001201"],
        },
        {
            "ontology_id": "CL:0000696",
            "name": "PP cell",
            "synonyms": "type F enteroendocrine cell",
            "children": ["CL:0002680"],
        },
        {
            "ontology_id": "CL:0002072",
            "name": "nodal myocyte",
            "synonyms": "cardiac pacemaker cell|myocytus nodalis|P cell",
            "children": ["CL:1000409", "CL:1000410"],
        },
    ]
    return pd.DataFrame.from_records(records)


def test_search_general(df):
    res = search(df=df, string="P cell", _show_rank=True)
    assert res.iloc[0]["name"] == "nodal myocyte"
    assert res.iloc[0]["rank"] == 223
    assert len(res) == 2
    assert res.iloc[1]["rank"] == 3

    # search in name, without synonyms search
    res = search(df=df, string="P cell", field="name", _show_rank=True)
    assert res.iloc[0]["name"] == "PP cell"
    assert res.iloc[0]["rank"] == 3


def test_search_limit(df):
    res = search(df=df, string="P cell", limit=1)
    assert res.shape[0] == 1


def test_search_return_df(df):
    res = search(df=df, string="P cell")
    assert res.shape == (2, 4)
    assert res.iloc[0]["name"] == "nodal myocyte"


def test_search_pass_fields(df):
    res = search(
        df=df,
        string="type F enteroendocrine",
        field=["synonyms", "children"],
        _show_rank=True,
    )
    assert res.iloc[0]["synonyms"] == "type F enteroendocrine cell"
    assert res.iloc[0]["rank"] == 15


def test_search_case_sensitive(df):
    res = search(df=df, string="b cell", case_sensitive=True)
    assert len(res) == 0
    res = search(df=df, string="b cell", case_sensitive=False, _show_rank=True)
    assert res.iloc[0]["name"] == "B cell"
    assert res.iloc[0]["rank"] == 438


def test_search_empty_df():
    res = search(pd.DataFrame(columns=["a", "b", "c"]), string="")
    assert res.shape == (0, 3)
