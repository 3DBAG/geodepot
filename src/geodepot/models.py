class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email


class Repository:
    def __init__(self, url: str = None):
        raise NotImplementedError


class Index:
    def __init__(self):
        self.cases = []

    def add_case(self, case):
        self.cases.append(case)

    def serialize(self):
        raise NotImplementedError

    def deserialize(self):
        raise NotImplementedError


class Case:
    def __init__(self, id: str, description: str = None):
        self.id = id
        self.description = description
        self.sha1 = None
        self.changed_by = None
        self.data_files = []

    def add_data_file(self, data_file):
        self.data_files.append(data_file)


