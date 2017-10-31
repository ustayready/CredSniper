class Config():
    def __init__(self):
        self.api_token = None
        self.module_name = None
        self.port = None
        self.enable_2fa = None
        self.creds = None
        self.seen = set()
        self.verbose = False
