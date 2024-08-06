import mule # pylint: disable=import-error

class ReplaceOperator(mule.DataOperator):
    """ Mule operator for replacing the data """
    def __init__(self):
        """Set up the replace operator"""
        pass
    def new_field(self, sources):
        """ Print the data from the new field """
        print('new_field')
        return sources[0]
    def transform(self, sources, result):
        """ Tranform the data """
        print('transform')
        return sources[1]
