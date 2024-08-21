from dataclasses import dataclass, field
from pathlib import Path
from typing import Self, NewType

from geodepot.config import User
from geodepot.data_file import DataFile, DataFileName

CaseName = NewType("CaseName", str)


@dataclass
class CaseSpec:
    """Case specifier."""

    case_name: CaseName | None = None
    data_file_name: DataFileName | None = None

    @classmethod
    def from_str(cls, casespec: str) -> Self:
        """Parse the case specifier."""
        return CaseSpec(*casespec.split("/"))

    def as_path(self) -> Path:
        if self.case_name is not None and self.data_file_name is not None:
            return Path(self.case_name, self.data_file_name)
        elif self.case_name is not None:
            return Path(self.case_name)
        else:
            Path()


@dataclass(repr=True)
class Case:
    name: CaseName
    description: str | None
    sha1: str | None = None
    data_files: dict[DataFileName, DataFile] = field(default_factory=dict)

    def add_from_path(self, source_path: Path, casespec: CaseSpec = None,
                      data_license: str = None, format: str = None,
                      description: str = None, changed_by: User = None) -> DataFile:
        df = DataFile(
            source_path,
            data_name=casespec.data_file_name if casespec is not None else None,
            data_license=data_license,
            data_format=format,
            description=description,
            changed_by=changed_by,
        )
        self.add_data_file(df)
        return df

    def add_data_file(self, data_file: DataFile):
        self.data_files[data_file.name] = data_file

    def get_data_file(self, name: DataFileName) -> DataFile | None:
        # TODO: maybe this should take a CaseSpec as argument instead of just a DataFileName
        return self.data_files.get(name)

    def remove_data_file(self, name: DataFileName) -> DataFile | None:
        return self.data_files.pop(name, None)

    def compress(self):
        raise NotImplementedError

    def extract(self):
        raise NotImplementedError
