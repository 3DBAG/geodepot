from dataclasses import dataclass, field
from pathlib import Path
from typing import Self, NewType

from geodepot.config import User, get_current_user
from geodepot.data import Data, DataName

CaseName = NewType("CaseName", str)


@dataclass
class CaseSpec:
    """Case specifier."""

    case_name: CaseName | None = None
    data_name: DataName | None = None

    @classmethod
    def from_str(cls, casespec: str) -> Self:
        """Parse the case specifier."""
        return CaseSpec(*casespec.split("/"))

    def to_path(self) -> Path:
        if self.case_name is not None and self.data_name is not None:
            return Path(self.case_name, self.data_name)
        elif self.case_name is not None:
            return Path(self.case_name)
        else:
            Path()


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

    def add_from_path(self, source_path: Path, casespec: CaseSpec = None,
                      data_license: str = None, data_format: str = None,
                      data_description: str = None, data_changed_by: User = None) -> Data:
        df = Data(source_path, data_license=data_license, data_format=data_format,
                  description=data_description, changed_by=data_changed_by,
                  data_name=casespec.data_name if casespec is not None else None)
        self.add_data(df)
        return df

    def add_data(self, data: Data):
        self.data[data.name] = data
        self.changed_by = data.changed_by

    def get_data(self, name: DataName) -> Data | None:
        # TODO: maybe this should take a CaseSpec as argument instead of just a DataName
        return self.data.get(name)

    def remove_data(self, name: DataName) -> Data | None:
        self.changed_by = get_current_user()
        return self.data.pop(name, None)

    def compress(self):
        raise NotImplementedError

    def extract(self):
        raise NotImplementedError
