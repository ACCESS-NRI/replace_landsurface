import mule # pylint: disable=import-error

class ReplaceOperator(mule.DataOperator):
    
    """ Mule operator for replacing the data"""
    def __init__(self):
        pass
        
    def new_field(self, sources):
        print('new_field')
        return sources[0]
        
    def transform(self, sources, result):
        print('transform')
        return sources[1]
