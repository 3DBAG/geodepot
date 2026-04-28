from dataclasses import dataclass, field
from logging import getLogger
from pathlib import Path
from typing import Self, NewType

from geodepot.config import User, get_current_user
from geodepot.data import Data, DataName

logger = getLogger(__name__)

CaseName = NewType("CaseName", str)


@dataclass(repr=True, order=True, unsafe_hash=True)
class CaseSpec:
    """Case specifier."""

    case_name: CaseName | None = None
    data_name: DataName | None = None

    def __str__(self):
        if self.data_name is None:
            return str(self.case_name)
        else:
            return f"{self.case_name}/{self.data_name}"

    @property
    def is_data(self):
        """Does the CaseSpec point to a data item?"""
        return self.case_name is not None and self.data_name is not None

    @property
    def is_case(self):
        """Does the CaseSpec point to a case?"""
        return self.case_name is not None and self.data_name is None

    def to_path(self) -> Path:
        if self.case_name is not None and self.data_name is not None:
            return Path(self.case_name, self.data_name)
        elif self.case_name is not None:
            return Path(self.case_name)
        else:
            Path()

    @classmethod
    def from_str(cls, casespec: str) -> Self:
        """Parse the case specifier."""
        parts = casespec.split("/")
        logger.debug("Parsing case specifier %s into %d part(s)", casespec, len(parts))
        parsed = CaseSpec(*parts)
        logger.debug(
            "Parsed case specifier %s as case=%s data=%s",
            casespec,
            parsed.case_name,
            parsed.data_name,
        )
        return parsed


@dataclass(repr=True, order=True)
class Case:
    """A test case.

    changed_by: The User that made the last modification on the case.
    """

    name: CaseName
    description: str | None
    sha1: str | None = None
    data: dict[DataName, Data] = field(default_factory=dict)
    changed_by: User | None = None

    def add_from_path(
        self,
        source_path: Path,
        casespec: CaseSpec = None,
        data_license: str = None,
        data_format: str = None,
        data_description: str = None,
        data_changed_by: User = None,
    ) -> Data:
        data = Data(
            source_path,
            data_license=data_license,
            data_format=data_format,
            description=data_description,
            changed_by=data_changed_by,
            data_name=casespec.data_name if casespec is not None else None,
        )
        logger.debug(
            "Adding data from %s to case %s as %s format=%s description_set=%s license_set=%s",
            source_path,
            self.name,
            data.name,
            data_format,
            data_description is not None,
            data_license is not None,
        )
        self.add_data(data)
        return data

    def add_data(self, data: Data):
        replaced = data.name in self.data
        self.data[data.name] = data
        self.changed_by = data.changed_by
        logger.debug(
            "Attached data %s to case %s replaced=%s total_data_items=%d",
            data.name,
            self.name,
            replaced,
            len(self.data),
        )

    def get_data(self, name: DataName) -> Data | None:
        # TODO: maybe this should take a CaseSpec as argument instead of just a DataName
        return self.data.get(name)

    def remove_data(self, name: DataName) -> Data | None:
        """Deletes the data item from the register of the Case."""
        logger.debug("Removing data %s from case %s", name, self.name)
        self.changed_by = get_current_user()
        removed = self.data.pop(name, None)
        if removed is None:
            logger.debug("No data %s found in case %s", name, self.name)
        else:
            logger.debug(
                "Removed data %s from case %s remaining_data_items=%d",
                name,
                self.name,
                len(self.data),
            )
        return removed

    def to_pretty(self) -> str:
        logger.debug(
            "Serializing case %s for display data_items=%d sha1_set=%s changed_by_set=%s",
            self.name,
            len(self.data),
            self.sha1 is not None,
            self.changed_by is not None,
        )
        output = [
            f"NAME={self.name}",
            f"\nDESCRIPTION={self.description}",
            f"\nnr_data_items={len(self.data)}",
            f"sha1={self.sha1}",
            f"changed_by={self.changed_by.to_pretty()}",
        ]
        return "\n".join(output)

    def compress(self):
        raise NotImplementedError

    def extract(self):
        raise NotImplementedError
