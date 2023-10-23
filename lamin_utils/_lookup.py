import re
from collections import namedtuple
from typing import Any, Dict, Iterable, List, Optional, Tuple

from ._logger import logger


def _append_records_to_list(df_dict: Dict, value: str, record) -> None:
    """Append unique records to a list."""
    values_list = df_dict[value]
    if not isinstance(values_list, list):
        values_list = [values_list]
    try:
        values_set = set(values_list)
        values_set.add(record)
        df_dict[value] = list(values_set)
    except TypeError:
        df_dict[value] = values_list


def _create_df_dict(
    df: Any = None,
    field: Optional[str] = None,
    records: Optional[List] = None,
    values: Optional[List] = None,
    tuple_name: Optional[str] = None,
) -> Dict:
    """Create a dict with {lookup key: records in namedtuple}.

    Value is a list of namedtuples if multiple records match the same key.
    """
    if df is not None:
        records = df.itertuples(index=False, name=tuple_name)
        values = df[field]
    df_dict: Dict = {}  # a dict of namedtuples as records and values as keys
    for i, row in enumerate(records):  # type:ignore
        value = values[i]  # type:ignore
        if not isinstance(value, str):
            continue
        if value == "":
            continue
        if value in df_dict:
            _append_records_to_list(df_dict=df_dict, value=value, record=row)
        else:
            df_dict[value] = row
    return df_dict


class Lookup:
    """Lookup object with dot and [] access."""

    # removed DataFrame type annotation to speed up import time
    def __init__(
        self,
        field: Optional[str] = None,
        tuple_name="MyTuple",
        prefix: str = "bt",
        df: Any = None,
        values: Optional[Iterable] = None,
        records: Optional[List] = None,
    ) -> None:
        self._tuple_name = tuple_name
        if df is not None:
            if df.shape[0] > 500000:
                logger.warning(
                    "generating lookup object from >500k keys is not recommended and"
                    " extremely slow"
                )
            values = df[field]
        self._df_dict = _create_df_dict(
            df=df,
            field=field,
            records=records,
            values=values,  # type:ignore
            tuple_name=self._tuple_name,
        )
        lkeys = self._to_lookup_keys(values=values, prefix=prefix)  # type:ignore
        self._lookup_dict = self._create_lookup_dict(lkeys=lkeys, df_dict=self._df_dict)
        self._prefix = prefix

    def _to_lookup_keys(self, values: Iterable, prefix: str) -> Dict:
        """Convert a list of strings to tab-completion allowed formats.

        Returns:
            {lookup_key: value_or_values}
        """
        lkeys: Dict = {}
        for value in list(values):
            if not isinstance(value, str):
                continue
            # replace any special character with _
            lkey = re.sub("[^0-9a-zA-Z_]+", "_", str(value)).lower()
            if lkey == "":  # empty strings are skipped
                continue
            if not lkey[0].isalpha():  # must start with a letter
                lkey = f"{prefix.lower()}_{lkey}"

            if lkey in lkeys:
                # if multiple values have the same lookup key
                # put the values into a list
                _append_records_to_list(df_dict=lkeys, value=lkey, record=value)
            else:
                lkeys[lkey] = value
        return lkeys

    def _create_lookup_dict(self, lkeys: Dict, df_dict: Dict) -> Dict:
        lkey_dict: Dict = {}  # a dict of namedtuples as records and lookup keys as keys
        for lkey, values in lkeys.items():
            if isinstance(values, list):
                combined_list = []
                for v in values:
                    records = df_dict.get(v)
                    if isinstance(records, list):
                        combined_list += records
                    else:
                        combined_list.append(records)
                lkey_dict[lkey] = combined_list
            else:
                lkey_dict[lkey] = df_dict.get(values)

        return lkey_dict

    def dict(self) -> Dict:
        """Dictionary of the lookup."""
        return self._df_dict

    def lookup(self, return_field: Optional[str] = None) -> Tuple:
        """Lookup records with dot access."""
        # Names are invalid if they are conflict with Python keywords.
        if "class" in self._lookup_dict:
            self._lookup_dict[f"{self._prefix.lower()}_class"] = self._lookup_dict.pop(
                "class"
            )
        keys: List = list(self._lookup_dict.keys()) + ["dict"]
        MyTuple = namedtuple("Lookup", keys)  # type:ignore
        if return_field is not None:
            self._lookup_dict = {
                k: v.__getattribute__(return_field)
                for k, v in self._lookup_dict.items()
            }
        return MyTuple(**self._lookup_dict, dict=self.dict)  # type:ignore
