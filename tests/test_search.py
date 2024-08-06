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


def test_search_synonyms(df):
    res = search(df=df, string="P cells")
    assert res.index[0] == "nodal myocyte"

    # without synonyms search
    res = search(df=df, synonyms_field=None, string="P cells")
    assert res.index[0] == "PP cell"


def test_search_limit(df):
    res = search(df=df, string="P cells", limit=1)
    assert res.shape[0] == 1


def test_search_keep(df):
    # TODO: better test here
    res = search(df=df, string="enteroendocrine", keep=False)
    assert res.index[0] == "PP cell"


def test_search_return_df(df):
    res = search(df=df, string="P cells")
    assert res.shape == (4, 4)
    assert res.iloc[0].name == "nodal myocyte"


def test_search_return_tie_results(df):
    res = search(df=df, string="A cell", synonyms_field=None)
    assert res.iloc[0].__ratio__ == res.iloc[1].__ratio__


def test_search_non_default_field(df):
    res = search(df=df, string="type F enteroendocrine", field="synonyms")
    assert res.index[0] == "type F enteroendocrine cell"


def test_search_case_sensitive(df):
    res = search(df=df, string="b cell", case_sensitive=True)
    assert res.iloc[0].__ratio__ < 100

    res = search(df=df, string="b cell", case_sensitive=False)
    assert res.index[0] == "B cell"
    assert res.iloc[0].__ratio__ == 100


def test_search_empty_df():
    res = search(pd.DataFrame(columns=["a", "b", "c"]), string="")
    assert res.shape == (0, 3)
