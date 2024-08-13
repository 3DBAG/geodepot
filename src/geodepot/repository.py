class Repository:
    def __init__(self, url: str = None):
        raise NotImplementedError


class Index:
    def __init__(self):
        self.cases = []

    def add_case(self, case):
        self.cases.append(case)

    def serialise(self):
        raise NotImplementedError

    def deserialise(self):
        raise NotImplementedError


