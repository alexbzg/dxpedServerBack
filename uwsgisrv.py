#!/usr/bin/python
#coding=utf-8

import json, logging
from urlparse import parse_qs
from datetime import datetime 

from common import siteConf, loadJSON


logging.basicConfig( level = logging.DEBUG,
        format='%(asctime)s %(message)s', 
        filename='/var/log/dxped_uwsgi.log',
        datefmt='%Y-%m-%d %H:%M:%S' )
conf = siteConf()
webRoot = conf.get( 'web', 'root' )

def application(env, start_response):
    try:
        reqSize = int( env.get( 'CONTENT_LENGTH', 0 ) )
    except:
        reqSize = 0

    start_response('200 OK', [('Content-Type','text/plain')])
    type = ( env["PATH_INFO"].split( '/' ) )[-1]
    postData = env['wsgi.input'].read( reqSize )
    newItem = {}
    data = []
    if type == 'news':
        newItem = parse_qs( postData )
        newItem['time'] = datetime.now().strftime( '%d %b %H:%M' ).lower()
        newItem['text'] = newItem['text'][0].decode('utf-8').replace( '\r\n', '<br/>' )
    else:
        newItem = json.loads( postData )
        if newItem.has_key( 'status' ):
            type = 'status'
            data = newItem['status']
            dt = datetime.utcnow()
            data['ts'] = int( dt.strftime("%s") ) * 1000
            data['date'] = dt.strftime( '%d %b' ).lower()
            data['time'] = dt.strftime( '%H:%Mz' )
        elif type == 'qso':
            dt = datetime.strptime( newItem['ts'], "%Y-%m-%d %H:%M:%S" )
            newItem['date'] = dt.strftime( '%d %b' ).lower()
            newItem['time'] = dt.strftime( '%H:%Mz' )
    fp = webRoot + '/' + type + '.json'
    if not data:
        data = loadJSON( fp )
        if not data:
            data = []
        data.insert( 0, newItem )
    with open( fp, 'w' ) as f:
        f.write( json.dumps( data, ensure_ascii = False ).encode('utf-8') )
    return 'OK'
       
