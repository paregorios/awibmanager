from os.path import isdir


class AI():
    """ barf """
    def __init__(self, id, path='.'):

        self.id = id
        if isdir(path):
            self.path = path
        else:
            raise IOError, "'%s' is not a directory" % path

