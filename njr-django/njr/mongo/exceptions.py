
class NJRError(Exception):
    pass

class NJRConfigError(NJRError):
    pass

class NJRArgumentError(NJRError):
    pass

class NJRDatabaseError(NJRError):
    pass
