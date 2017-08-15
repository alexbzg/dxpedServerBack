#!/usr/bin/python
#coding=utf-8

import json, logging, os, shutil, math
from urlparse import parse_qs
from datetime import datetime 

from common import siteConf, loadJSON


logging.basicConfig( level = logging.DEBUG,
        format='%(asctime)s %(message)s', 
        filename='/var/log/dxped_uwsgi.log',
        datefmt='%Y-%m-%d %H:%M:%S' )
logging.debug( "restart" )
conf = siteConf()
webRoot = conf.get( 'web', 'root' )
regCS = conf.get( 'web', 'regCS' ).split(',')

def dtFmt( dt ):
    return dt.strftime( '%d %b' ).lower(), dt.strftime( '%H:%Mz' )

def sind( d ):
    return math.sin( math.radians(d) )

def cosd( d ):
    return math.cos( math.radians(d) )


def updateLocation( newData ):
    fp = webRoot + '/location.json'
    data = loadJSON( fp )
    if not data:
        data = {}
    if not data.has_key( 'locTs' ) and data.has_key( 'ts' ):
        data['locTs'] = data['ts']
    data['ts'] = int( datetime.now().strftime("%s") ) 
    data['date'], data['time'] = dtFmt( datetime.utcnow() )    
    if newData['location']:
        if data.has_key( 'location' ) and data['location']:
            data['prev'] = { 'location': data['location'][:], \
                    'ts': data['locTs'] }
        data['locTs'] = data['ts']
        data['location'] = newData['location']
        data['loc'] = newData['loc']
        data['rafa'] = newData['rafa']
        if data.has_key( 'prev' ):
            lat = [data['location'][1], data['prev']['location'][1]]
            lon = [data['location'][0], data['prev']['location'][0]]
            dlon = lon[0] - lon[1] 
            dlat = lat[0] - lat[1] 
            a = (sind(dlat/2))**2 + cosd(lat[0]) * cosd(lat[1]) * (sind(dlon/2)) ** 2
            c = 2 * math.atan2( math.sqrt(a), math.sqrt(1-a) ) 
            d = c * 6373            
            data['d'] = d
            data['dt'] = data['locTs'] - data['prev']['ts']
            data['speed'] = d / ( float( data['locTs'] - data['prev']['ts'] ) / 3600 )
    with open( fp, 'w' ) as f:
        f.write( json.dumps( data, ensure_ascii = False ).encode('utf-8') )


def application(env, start_response):
    try:
        reqSize = int( env.get( 'CONTENT_LENGTH', 0 ) )
    except:
        reqSize = 0

    type = ( env["PATH_INFO"].split( '/' ) )[-1]
    if type == 'clearLog':
        os.remove( webRoot + '/qso.json' )
        start_response('302 Found', [('Location','http://73.ru/rda/')])
        return
  
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
            updateLocation( newItem )
            start_response('200 OK', [('Content-Type','text/plain')])
            return 'OK'
           
            if not newItem['location']:
                prev = loadJSON( webRoot + '/location.json' )
                if prev:
                    newItem['location'] = prev['location']

            type = 'location'
            data = newItem
            data['ts'] = int( datetime.now().strftime("%s") ) 
            data['locTs'] = data['ts']
            data['date'], data['time'] = dtFmt( datetime.utcnow() )
           
        elif type == 'qso':
            logging.debug( newItem )
            fp = webRoot + '/qso.json'
            data = loadJSON( fp )
            if not data and os.path.isfile( fp ):
                bakNo = 0
                bakFp = fp + '.bak'
                while os.path.isfile( bakFp ):
                    bakNo += 1
                    bakFp += str( bakNo )
                shutil.copyfile( fp, bakFp )
                data = []
            data.insert( 0, newItem )
            dt = datetime.strptime( newItem['ts'], "%Y-%m-%d %H:%M:%S" )
            if newItem['rda']:
                newItem['rda'] = newItem['rda'].upper()
            if newItem['wff']:
                newItem['wff'] = newItem['wff'].upper()
            newItem['date'], newItem['time'] = dtFmt( dt )
            locFp = webRoot + '/location.json'
            locData = loadJSON( locFp )
            if not locData:
                locData = {}
            locData['ts'] = int( datetime.now().strftime("%s") ) 
            with open( locFp, 'w' ) as f:
                f.write( json.dumps( locData, ensure_ascii = False ).encode('utf-8') )

        elif type == 'chat' or type == 'users':
            newItem['cs'] = newItem['cs'].upper()
            pwd = newItem['cs'].endswith(':123')
            if pwd:
                newItem['cs'] = newItem['cs'][:-4]
                if newItem['cs'] in regCS:
                    newItem['admin'] = True
            if newItem['cs'] in regCS and not pwd:
                start_response('403 Forbidden' )
                return 'This callsign is password protected'
            if type == 'chat':
                newItem['date'], newItem['time'] = dtFmt( datetime.utcnow() )
            elif type == 'users':
                fp = webRoot + '/users.json'
                data = loadJSON( fp )
                if not data:
                    data = {}
                if newItem.has_key('delete'): 
                    if data.has_key(newItem['cs']):
                        del data[newItem['cs']]
                else:
                    data[newItem['cs']] = { 'tab': newItem['tab'], \
                            'ts': int( datetime.now().strftime("%s") ) }
                with open( fp, 'w' ) as f:
                    f.write( json.dumps( data, ensure_ascii = False ).encode('utf-8') )
                start_response('200 OK', [('Content-Type','text/plain')])
                return 'OK'

           

    fp = webRoot + '/' + type + '.json'
    if not data:
        data = loadJSON( fp )
        if not data:
            data = []
        data.insert( 0, newItem )
    with open( fp, 'w' ) as f:
        f.write( json.dumps( data, ensure_ascii = False ).encode('utf-8') )
    if type == 'news':
        start_response('302 Found', [('Location','http://73.ru/rda/')])
        return
    else:
        start_response('200 OK', [('Content-Type','text/plain')])
        return 'OK'
       
