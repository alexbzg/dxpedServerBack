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

def dtFmt( dt ):
    return dt.strftime( '%d %b' ).lower(), dt.strftime( '%H:%Mz' )


def application(env, start_response):
    try:
        reqSize = int( env.get( 'CONTENT_LENGTH', 0 ) )
    except:
        reqSize = 0

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
        if newItem.has_key( 'location' ):
            type = 'location'
            data = newItem
            data['date'], data['time'] = dtFmt( datetime.utcnow() )
        elif type == 'qso':
            dt = datetime.strptime( newItem['ts'], "%Y-%m-%d %H:%M:%S" )
            newItem['date'], newItem['time'] = dtFmt( dt )
        elif type == 'chat':
            newItem['date'], newItem['time'] = dtFmt( datetime.utcnow() )

    fp = webRoot + '/' + type + '.json'
    if not data:
        data = loadJSON( fp )
        if not data:
            data = []
        data.insert( 0, newItem )
    with open( fp, 'w' ) as f:
        f.write( json.dumps( data, ensure_ascii = False ).encode('utf-8') )
    if type == 'news':
        start_response('302 Found', [('Location','http://73.com/rda/index2.html')])
        return
    else:
        start_response('200 OK', [('Content-Type','text/plain')])
        return 'OK'
       
