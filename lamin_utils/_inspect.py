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
    case_sensitive: bool = True,
    **kwargs,
) -> "np.ndarray":
    """Check if an iterable is in a list of values with case sensitive option."""
    import pandas as pd

    identifiers_idx = pd.Index(identifiers)
    identifiers_idx = to_str(identifiers_idx, case_sensitive=case_sensitive)

    field_values = to_str(field_values, case_sensitive=case_sensitive)

    # annotated what complies with the default ID
    matches = identifiers_idx.isin(field_values)
    if kwargs.get("return_df") is True:
        validated_df = pd.DataFrame(index=identifiers)
        validated_df["__validated__"] = matches
        return validated_df
    else:
        return matches


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

    def unique_rm_empty(idx: pd.Index):
        idx = idx.unique()
        return idx[(idx != "") & (~idx.isnull())]

    uniq_identifiers = unique_rm_empty(pd.Index(identifiers)).tolist()
    # empty DataFrame or input
    if df.shape[0] == 0 or len(uniq_identifiers) == 0:
        validated_df = pd.DataFrame(index=identifiers, data={"__validated__": False})
        result = InspectResult(validated_df, [], uniq_identifiers, frac_validated=0.0)
        if kwargs.get("return_df") is True:
            return result.df
        else:
            return result

    # check if index is compliant with exact matches
    validated_df = validate(
        identifiers=identifiers,
        field_values=df[field],
        case_sensitive=True,
        return_df=True,
    )

    # check without being case sensitive
    validated_df_noncs = validate(
        identifiers=identifiers,
        field_values=df[field],
        case_sensitive=False,
        return_df=True,
    )
    casing_warn_msg = ""
    if validated_df_noncs["__validated__"].sum() > validated_df["__validated__"].sum():
        casing_warn_msg = f"🟠 detected {colors.yellow('inconsistent casing')}"

    validated = unique_rm_empty(
        validated_df.index[validated_df["__validated__"]]
    ).tolist()
    nonvalidated = unique_rm_empty(
        validated_df.index[~validated_df["__validated__"]]
    ).tolist()

    synonyms_warn_msg = ""
    # backward compat
    if kwargs.get("inspect_synonyms") is not False:
        try:
            synonyms_mapper = map_synonyms(
                df=df,
                identifiers=nonvalidated,
                field=field,
                return_mapper=True,
                case_sensitive=False,
            )
            if len(synonyms_mapper) > 0:
                synonyms_warn_msg = f"🟠 detected {colors.yellow('synonyms')}"
        except Exception:
            pass

    n_unique_terms = len(validated) + len(nonvalidated)
    n_empty = len(list(identifiers)) - n_unique_terms
    frac_nonvalidated = round(len(nonvalidated) / n_unique_terms * 100, 1)
    frac_validated = 100 - frac_nonvalidated

    if not mute:
        if n_empty > 0:
            logger.warning(
                f"received {n_unique_terms} unique terms, {n_empty} empty/duplicated"
                " terms are ignored"
            )
        logger.success(f"{len(validated)} terms ({frac_validated:.2f}%) are validated")
        if frac_validated < 100:
            warn_msg = (
                f"{len(nonvalidated)} terms ({frac_nonvalidated:.2f}%) are not"
                " validated"
            )
            hint = False
            if len(casing_warn_msg) > 0:
                warn_msg += f"\n   {casing_warn_msg}"
                hint = True
            if len(synonyms_warn_msg) > 0:
                warn_msg += f"\n   {synonyms_warn_msg}"
                hint = True
            if hint:
                warn_msg += (
                    "\n   to increase validated terms, standardize them via"
                    f" {colors.green('.map_synonyms()')}"
                )

            logger.warning(warn_msg)

    result = InspectResult(validated_df, validated, nonvalidated, frac_validated)
    # backward compat
    if kwargs.get("return_df") is True:
        return result.df

    return result


class InspectResult:
    """Result of inspect."""

    def __init__(
        self,
        validated_df,
        validated: List[str],
        nonvalidated: List[str],
        frac_validated: float,
    ) -> None:
        self._df = validated_df
        self._validated = validated
        self._non_validated = nonvalidated
        self._frac_validated = frac_validated

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
