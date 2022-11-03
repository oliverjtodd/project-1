
class NoData(Exception):
    pass

class NoHeaders(Exception):
    pass

class InvalidKeyForm(Exception):
    pass

class UnAuthed(Exception):
    pass

class NoHeaders(Exception):
    pass

class NoHeaders(Exception):
    pass

class Ban(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'
class Auth:
    class Ban(Exception):
        def __init__(self, message):
            self.message = message
            super().__init__(self.message)

        def __str__(self):
            return f'{self.message}'
    
    class WrongHWID(Exception):
        pass

    class NoHeaders(Exception):
        pass

    class NoVersion(Exception):
        pass
    
    class InvalidUserAgent(Exception):
        pass
    
    class InvalidKeyForm(Exception):
        pass

    class Outdated(Exception):
        pass

    class UnAuthorised(Exception):
        def __init__(self, message):
            self.message = message
            super().__init__(self.message)

        def __str__(self):
            return f'{self.message}'