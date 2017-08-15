#!/usr/bin/python
#coding=utf-8


import json, logging

from common import siteConf, loadJSON


logging.basicConfig( level = logging.DEBUG,
        format='%(asctime)s %(message)s', 
        filename='/var/log/dxped_getSpots.log',
        datefmt='%Y-%m-%d %H:%M:%S' )
conf = siteConf()
webRoot = conf.get( 'web', 'root' )
spotsSrcF = conf.get( 'adxcluster', 'spots' )

spotsF = webRoot + '/spots.json'
newData = loadJSON( spotsSrcF )
if not newData:
    logging.error( 'Spots data is empty' )
    raise SystemExit
newData = [ x for x in newData \
        if x['country'] == 'Russia' and \
        ( x['cs'].endswith( '/M' ) or x['cs'].endswith('/P') \
        or x['cs'].endswith('/MM') ) ]
data = loadJSON( spotsF )
if not data:
    data =[]
prev = data[0] if data else None
idx = 0
for item in reversed(newData):
    if prev and item['ts'] <= prev['ts']:
        break
    data.insert( idx, item )
    idx += 1
if len( data ) > 20:
    data = data[:20]
with open( spotsF, 'w' ) as f:
    f.write( json.dumps( data, ensure_ascii = False ).encode('utf-8') )

