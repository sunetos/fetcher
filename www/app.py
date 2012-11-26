#!/usr/bin/env python

from gevent import monkey; __name__ == '__main__' and monkey.patch_all()

from bottle import redirect, request, route, run, jinja2_view as view
from oauth_hook import OAuthHook
import requests
import json
from setproctitle import setproctitle
import yaml

from fetcher import AttrDict


CFG = AttrDict(yaml.load(open('www/cfg.yml', 'r')))


@route('/api/auth')
@view('www/views/oauth')
def auth_putio():
  code = request.GET.get('code')
  if code:
    resp = requests.get('https://api.put.io/v2/oauth2/access_token', params={
        'client_id': CFG.oauth.client_id,
        'client_secret': CFG.oauth.client_secret,
        'grant_type': 'authorization_code',
        'redirect_uri': CFG.oauth.callback,
        'code': code,
    })
    if resp.status_code != 200:
      abort(500, 'Sorry, put.io may be currently experiencing issues.')

    data = json.loads(resp.text)
    return {'token': data['access_token']}
  else:
    req = requests.Request('https://api.put.io/v2/oauth2/authenticate', params={
        'client_id': CFG.oauth.client_id,
        'response_type': 'code',
        'redirect_uri': CFG.oauth.callback,
    })
    return {'url': req.full_url}


if __name__ == '__main__':
  setproctitle('fetcher-www')
  run(host='0.0.0.0', port=12000, server='gevent')
