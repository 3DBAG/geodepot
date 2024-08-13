class Case:
    def __init__(self, id: str, description: str = None):
        self.id = id
        self.description = description
        self.sha1 = None
        self.changed_by = None
        self.data_files = []
        # todo: need to create case directory if not exists

    def add_data_file(self, data_file):
        # todo: need to move the data file to the case dir
        self.data_files.append(data_file)

    def compress(self):
        raise NotImplementedError

    def extract(self):
        raise NotImplementedError
