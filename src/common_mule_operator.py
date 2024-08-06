"""Module providing a function to replace data in a fieldsfile."""
import mule # pylint: disable=import-error

class ReplaceOperator(mule.DataOperator):
    """ Mule operator for replacing the data """
    def __init__(self):
        """Set up the replace operator"""
    def new_field(self, sources):
        """ Print the data from the new field """
        print('new_field')
        return sources[0]
    def transform(self, sources, result): # pylint: disable=unused-argument
        """ Tranform the data """
        print('transform')
        return sources[1]
