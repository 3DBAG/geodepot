from dataclasses import dataclass, field
from pathlib import Path
from typing import Self, NewType

from geodepot.config import User
from geodepot.data_file import DataFile

CaseId = NewType("CaseId", str)


@dataclass
class CaseSpec:
    """Case specifier."""

    case_id: CaseId | None = None
    data_file_name: str | None = None

    @classmethod
    def from_str(cls, casespec: str) -> Self:
        """Parse the case specifier."""
        return CaseSpec(*casespec.split("/"))


@dataclass(repr=True)
class Case:
    id: CaseId
    description: str
    sha1: str = None
    data_files: list[DataFile] = field(default_factory=list)
    # todo: need to create case directory if not exists

    def add_path(
        self,
        path: Path,
        data_license: str = None,
        format: str = None,
        description: str = None,
        changed_by: User = None,
    ) -> DataFile:
        df = DataFile(
            path,
            data_license=data_license,
            data_format=format,
            description=description,
            changed_by=changed_by,
        )
        self.add_data_file(df)
        return df

    def add_data_file(self, data_file):
        # todo: need to move the data file to the case dir
        self.data_files.append(data_file)

    def compress(self):
        raise NotImplementedError

    def extract(self):
        raise NotImplementedError
