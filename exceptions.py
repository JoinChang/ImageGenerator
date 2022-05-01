class ResourceFileNotFound(Exception):
    def __init__(self, id):
        self.id = id

class ConfigFileNotFound(Exception):
    def __init__(self, id):
        self.id = id

class UnknownGenerateType(Exception):
    def __init__(self, type):
        self.type = type

class UnmatchedPositionType(Exception):
    def __init__(self, position, type):
        self.position = position
        self.type = type

class ReachMaxLineException(Exception):
    def __init__(self, position, max_line):
        self.position = position
        self.max_line = max_line