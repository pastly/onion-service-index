#!/usr/bin/env python3
import random
from flask import Flask
from flask import abort, make_response, redirect, render_template, request

app = Flask(__name__)

base32_chars = [ c for c in '234567abcdefghijklmnopqrstuvwxyz' ]
page_length = 128
num_onions = 32**16

def num_to_base(n, b=10, min_length=0):
    #if n == 0: return [0]
    digits = []
    while n:
        digits.append(int(n % b))
        n //= b
    if len(digits) < min_length:
        num_zeros = min_length - len(digits)
        digits.extend([0] * num_zeros)
    return digits[::-1]

def translate_with_lookup(digits, lookup):
    return ''.join([ lookup[d] for d in digits])

def get_page_nav(current_page):
    start = current_page - 10
    if start < 1:
        start = 1
    end = current_page + 10
    if end > num_onions / page_length:
        end = int(num_onions / page_length)
    return [ i for i in range(start, end+1) ]

def gen_page(page=1, do_cache=True):
    if page < 1: page = 1
    if page > num_onions / page_length:
        page = int(num_onions / page_length)
    start = (page - 1) * page_length
    end = page * page_length
    onions = [ num_to_base(o, 32, 16) for o in range(start, end) ]
    onions = [ translate_with_lookup(o, base32_chars) for o in onions]
    nav = get_page_nav(page)
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
    return gen_page(page)

@app.route('/random', methods=['GET'])
def random_():
    if request.method != 'GET': abort(405)
    min_page = 1
    max_page = int(num_onions / page_length)
    page = random.randint(min_page, max_page)
    return redirect("?page={}".format(page), code=302)

if __name__ == '__main__':
    #app.debug = True
    app.jinja_env.globals['app_name'] = 'All Onion Services'
    app.jinja_env.globals['num_onions'] = format(num_onions, ',')
    app.jinja_env.globals['last_page'] = int(num_onions / page_length)
    app.run(host='localhost', port=8765)
