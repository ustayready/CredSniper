class BaseModule(object):
    def __init__(self, enable_2fa=False):
        self.env = None
        self.name = None
        self.user = None
        self.password = None
        self.two_factor_token = None
        self.two_factor_type = None
        self.enable_2fa = None
        self.final_url = None
        self.routes = []


    def set_name(self, name):
        '''Set the name of the module, it will be used during the import process.'''
        self.name = name

    def enable_two_factor(self, enabled):
        '''Enable checking 2FA within the module'''
        self.enable_2fa = enabled


    def set_two_factor(self, two_factor_token, two_factor_type):
        '''Sets the two factor information after triggering an authenticated login using the credentials.'''
        self.two_factor_token = two_factor_token
        self.two_factor_type = two_factor_type


    def set_creds(self, user, password):
        '''Sets the username and password after capturing them from the phishing page. '''
        self.user = user
        self.password = password


    def add_route(self, name, url):
        '''Add a route to the module for each templated page. Each route name will reference a function in the module and the url will correspond to the URI path of the URL. (i.e. name: Authenticate, url: /authenticate)
        '''
        route = {}
        route['name'] = name
        route['url'] = url
        self.routes.append(route)
