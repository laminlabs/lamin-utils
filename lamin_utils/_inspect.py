from typing import TYPE_CHECKING, Iterable, List

from ._core import colors
from ._logger import logger
from ._map_synonyms import map_synonyms, to_str

if TYPE_CHECKING:
    import numpy as np
    import pandas as pd


def validate(
    identifiers: Iterable,
    field_values: Iterable,
    *,
    case_sensitive: bool = True,
    mute: bool = False,
    **kwargs,
) -> "np.ndarray":
    """Check if an iterable is in a list of values with case sensitive option."""
    if isinstance(kwargs.get("logging"), bool):
        mute = not kwargs.get("logging")
    import pandas as pd

    identifiers_idx = pd.Index(identifiers)
    identifiers_idx = to_str(identifiers_idx, case_sensitive=case_sensitive)

    field_values = to_str(field_values, case_sensitive=case_sensitive)

    # annotated what complies with the default ID
    matches = identifiers_idx.isin(field_values)
    if not mute:
        _validate_logging(_validate_stats(identifiers=identifiers, matches=matches))
    return matches


def _unique_rm_empty(idx: "pd.Index"):
    idx = idx.unique()
    return idx[(idx != "") & (~idx.isnull())]


def _validate_stats(identifiers: Iterable, matches: "np.ndarray"):
    import pandas as pd

    df_val = pd.DataFrame(data={"__validated__": matches}, index=identifiers)
    val = _unique_rm_empty(df_val.index[df_val["__validated__"]]).tolist()
    nonval = _unique_rm_empty(df_val.index[~df_val["__validated__"]]).tolist()

    n_unique = len(val) + len(nonval)
    n_empty = df_val.shape[0] - n_unique
    frac_nonval = round(len(nonval) / n_unique * 100, 1)
    frac_val = 100 - frac_nonval

    return InspectResult(
        validated_df=df_val,
        validated=val,
        nonvalidated=nonval,
        frac_validated=frac_val,
        n_empty=n_empty,
        n_unique=n_unique,
    )


def _validate_logging(result: "InspectResult"):
    """Logging of the validated result."""
    if result.n_empty > 0:
        unique_s = "" if result.n_unique == 1 else "s"
        empty_s = " is" if result.n_empty == 1 else "s are"
        logger.warning(
            f"received {result.n_unique} unique term{unique_s},"
            f" {result.n_empty} empty/duplicated term{empty_s} ignored"
        )
    s = "" if len(result.validated) == 1 else "s"
    are = "is" if len(result.validated) == 1 else "are"
    logger.success(
        f"{len(result.validated)} term{s} ({result.frac_validated:.2f}%)"
        f" {are} validated"
    )
    if result.frac_validated < 100:
        s = "" if len(result.non_validated) == 1 else "s"
        are = "is" if len(result.non_validated) == 1 else "are"
        warn_msg = (
            f"{len(result.non_validated)} term{s} ({(100-result.frac_validated):.2f}%)"
            f" {are} not validated"
        )
        logger.warning(warn_msg)


def inspect(
    df: "pd.DataFrame",
    identifiers: Iterable,
    field: str,
    *,
    mute: bool = False,
    **kwargs,
) -> "InspectResult":
    """Inspect if a list of identifiers are mappable to the entity reference.

    Args:
        identifiers: Identifiers that will be checked against the field.
        field: The BiontyField of the ontology to compare against.
                Examples are 'ontology_id' to map against the source ID
                or 'name' to map against the ontologies field names.
        return_df: Whether to return a Pandas DataFrame.

    Returns:
        InspectResult object
    """
    # backward compat
    if isinstance(kwargs.get("logging"), bool):
        mute = not kwargs.get("logging")
    import pandas as pd

    uniq_identifiers = _unique_rm_empty(pd.Index(identifiers)).tolist()
    # empty DataFrame or input
    if df.shape[0] == 0 or len(uniq_identifiers) == 0:
        result = _validate_stats(
            identifiers=identifiers, matches=[False] * len(identifiers)  # type:ignore
        )
        if kwargs.get("return_df") is True:
            return result.df
        else:
            return result

    # check if index is compliant with exact matches
    matches = validate(
        identifiers=identifiers, field_values=df[field], case_sensitive=True, mute=True
    )
    # matches if case sensitive is turned off
    noncs_matches = validate(
        identifiers=identifiers, field_values=df[field], case_sensitive=False, mute=True
    )

    casing_warn_msg = ""
    if noncs_matches.sum() > matches.sum():
        casing_warn_msg = f"🟠 detected {colors.yellow('inconsistent casing')}"

    result = _validate_stats(identifiers=identifiers, matches=matches)

    synonyms_warn_msg = ""
    # backward compat
    if kwargs.get("inspect_synonyms") is not False:
        try:
            synonyms_mapper = map_synonyms(
                df=df,
                identifiers=result.non_validated,
                field=field,
                return_mapper=True,
                case_sensitive=False,
            )
            if len(synonyms_mapper) > 0:
                synonyms_warn_msg = f"🟠 detected {colors.yellow('synonyms')}"
        except Exception:
            pass

    if not mute:
        _validate_logging(result=result)
        warn_msg = ""
        hint = False
        if len(casing_warn_msg) > 0:
            warn_msg += f"\n   {casing_warn_msg}"
            hint = True
        if len(synonyms_warn_msg) > 0:
            warn_msg += f"\n   {synonyms_warn_msg}"
            hint = True
        if hint:
            warn_msg += (
                "\n   to increase validated terms, run"
                f" {colors.green('.standardize()')}"
            )
        if len(warn_msg) > 0:
            logger.warning(warn_msg)

    # backward compat
    if kwargs.get("return_df") is True:
        return result.df

    return result


class InspectResult:
    """Result of inspect."""

    def __init__(
        self,
        validated_df: "pd.DataFrame",
        validated: List[str],
        nonvalidated: List[str],
        frac_validated: float,
        n_empty: int,
        n_unique: int,
    ) -> None:
        self._df = validated_df
        self._validated = validated
        self._non_validated = nonvalidated
        self._frac_validated = frac_validated
        self._n_empty = n_empty
        self._n_unique = n_unique

    @property
    def df(self) -> "pd.DataFrame":
        """A DataFrame indexed by values with a boolean `__validated__` column."""  # noqa
        return self._df

    @property
    def validated(self) -> List[str]:
        return self._validated

    @property
    def non_validated(self) -> List[str]:
        return self._non_validated

    @property
    def frac_validated(self) -> float:
        return self._frac_validated

    @property
    def n_empty(self) -> int:
        return self._n_empty

    @property
    def n_unique(self) -> int:
        return self._n_unique

    def __getitem__(self, key) -> List[str]:
        """Bracket access to the inspect result."""
        if key == "validated":
            return self.validated
        elif key == "non_validated":
            return self.non_validated
        # backward compatibility below
        elif key == "mapped":
            return self.validated
        elif key == "not_mapped":
            return self.non_validated
        else:
            raise KeyError("invalid key")
