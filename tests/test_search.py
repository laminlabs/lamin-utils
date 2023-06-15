import pytest

from lamin_logger._search import search


@pytest.fixture(scope="module")
def df():
    import pandas as pd

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


def test_search_name_default(df):
    res = search(df=df, string="T cells", tuple_name="MyTuple")
    assert res.name == "T cell"
    assert res.ontology_id == "CL:0000084"
    assert res.children == ["CL:0000798", "CL:0002420", "CL:0002419", "CL:0000789"]
    assert res.synonyms == "T-cell|T lymphocyte|T-lymphocyte"
    assert res.__class__.__name__ == "MyTuple"


def test_search_synonyms(df):
    res = search(df=df, string="P cells")
    assert res.name == "nodal myocyte"

    res = search(df=df, synonyms_field=None, string="P cells")
    assert res.name == "PP cell"


def test_search_return_df(df):
    res = search(df=df, string="P cells", return_ranked_results=True)
    assert res.shape == (4, 4)
    assert res.iloc[0].name == "nodal myocyte"


def test_search_return_tie_results(df):
    res = search(df=df, string="A cell", synonyms_field=None)
    assert len(res) == 2


def test_search_non_default_field(df):
    res = search(df=df, string="type F enteroendocrine", field="synonyms")
    res.synonyms == "type F enteroendocrine cell"
