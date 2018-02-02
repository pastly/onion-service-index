#!/usr/bin/env python3
import random
from flask import Flask
from flask import abort, make_response, redirect, render_template, request
from hashlib import sha3_256
import base64
import ed25519

app = Flask(__name__)

BASE32_CHARS = list('abcdefghijklmnopqrstuvwxyz234567')
PAGE_LENGTH = 128
NUM_ONIONS = 32**16, 2**(32*8)

app.debug = False
app.jinja_env.globals.update({
    'app_name': 'All Onion Services',
    'num_onions': NUM_ONIONS,
    'page_length': PAGE_LENGTH
})


class V2Onion:
    def __init__(self, num):
        self._num = num
        self._str = V2Onion.int_to_onion_addr(num)

    @staticmethod
    def int_to_onion_addr(num):
        digits = []
        base = 32
        length = 16
        while num:
            digits.append(int(num % base))
            num //= base
        if len(digits) < length:
            num_zeros = length - len(digits)
            digits.extend([0] * num_zeros)
        return ''.join([BASE32_CHARS[d] for d in digits[::-1]])

    def __str__(self):
        return self._str


class V3Onion:
    def __init__(self, num):
        self._num = num
        self._str = V3Onion.int_to_onion_addr(num)

    @staticmethod
    def int_to_onion_addr(num):
        master = num.to_bytes(32, byteorder='big')
        signing_key = ed25519.SigningKey(master)
        verifying_key = signing_key.get_verifying_key().to_bytes()
        version = b'\x03'
        prefix = b'.onion checksum'
        checksum = sha3_256(prefix + verifying_key + version).digest()[:2]
        addr_as_bytes = verifying_key + checksum + version
        addr = base64.b32encode(addr_as_bytes)
        return addr.decode('utf-8').lower()

    def __str__(self):
        return self._str


def get_page_url(page=1, v3=False):
    return '?page=%s' % page + ('&amp;v3' if v3 else '')


app.jinja_env.globals['get_page_url'] = get_page_url


def get_page_nav(current_page, v3=False):
    start = current_page - 10
    num_onions = NUM_ONIONS[v3]
    if start < 1:
        start = 1
    end = current_page + 10
    if end > num_onions / PAGE_LENGTH:
        end = num_onions // PAGE_LENGTH
    return range(start, end+1)


def gen_page(page=1, v3=False, do_cache=True):
    num_onions = NUM_ONIONS[v3]
    if page < 1:
        page = 1
    if page > num_onions / PAGE_LENGTH:
        print(page, 'page too big. setting to', num_onions // PAGE_LENGTH)
        page = num_onions // PAGE_LENGTH
    start = (page - 1) * PAGE_LENGTH
    end = page * PAGE_LENGTH
    if not v3:
        onions = [V2Onion(o) for o in range(start, end)]
    else:
        onions = [V3Onion(o) for o in range(start, end)]
    nav = get_page_nav(page, v3)
    resp = make_response(render_template('index.html.j2',
        onions=onions, page=page, nav=nav))
    if do_cache: resp.headers['Cache-Control'] = 'max-age=600'
    return resp

@app.route('/', methods=['GET'])
def index_():
    if request.method != 'GET': abort(405)
    page = 1
    if 'page' in request.args:
        try: page = int(request.args['page'])
        except ValueError: page = 1
    v3 = 'v3' in request.args
    return gen_page(page, v3)

@app.route('/random', methods=['GET'])
def random_():
    if request.method != 'GET': abort(405)
    v3 = 'v3' in request.args
    num_onions = NUM_ONIONS[v3]
    max_page = num_onions // PAGE_LENGTH
    page = random.randint(1, max_page)
    page_url = '?page={}'
    if v3: page_url += '&v3'
    return redirect(page_url.format(page), code=302)


if __name__ == '__main__':
    app.run(host='localhost', port=8765)
