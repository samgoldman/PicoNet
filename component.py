   

class Component():
    def __init__(self):
        raise NotImplementedError()

    def run_periodic(self):
        '''
        This function is guaranteed to be called at least every 1/10th of a second
        '''
        raise NotImplementedError()

    def process_packet(self):
        raise NotImplementedError()

    def get_subscriptions(self):
        raise NotImplementedError()
