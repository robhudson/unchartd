import os
import sys
import urllib
import urlparse

import dateutil.parser
import elasticsearch
import requests


es = elasticsearch.Elasticsearch(['localhost:9200'])


ES_INDEX = 'unchartd'
ES_DOCTYPE = 'checkins'


UNTAPPD_ENDPOINT = 'http://api.untappd.com/v4'


try:
    UNTAPPD_USERNAME = os.environ['UNTAPPD_USERNAME']
except KeyError:
    print "The environment variable, 'UNTAPPD_USERNAME', was not found."
    print "Export your untappd username you'd like to gather data for by"
    print "running this command first and try again:"
    print "export UNTAPPD_USERNAME='your_username'"
    exit()


try:
    UNTAPPD_CLIENT_ID = os.environ['UNTAPPD_CLIENT_ID']
    UNTAPPD_CLIENT_SECRET = os.environ['UNTAPPD_CLIENT_SECRET']
except KeyError:
    print "One of the environment variables for accessing the Untappd API was"
    print "not found. Execute the following with your Untappd API credentials:"
    print "export UNTAPPD_CLIENT_ID='<client_id>'"
    print "export UNTAPPD_CLIENT_SECRET='<client_secret>'"
    print
    print "If you need credentials visit https://untappd.com/api/dashboard"
    exit()


if es.indices.exists(ES_INDEX):
    print "This script was run once before. If you'd like to run it again "
    print "delete the index by running the following:"
    print "curl -XDELETE http://localhost:9200/%s" % ES_INDEX
    exit()

es.indices.create(ES_INDEX, {
    "settings": {
        "index": {
            "number_of_replicas": 0
        }
    }
})


# We override some mapping types to more easily query the data later.
es.indices.put_mapping(ES_INDEX, ES_DOCTYPE, {
    "checkins": {
        "properties": {
            "beer": {
                "properties": {
                    "beer_style": {
                        "type": "multi_field",
                        "fields": {
                            "beer_style": {"type": "string",
                                           "index": "analyzed"},
                            "style_facet": {"type": "string",
                                            "index": "not_analyzed"}
                        }
                    }
                }
            }
        }
    }
})


def _url(url, **qs):
    url = url % {'UNTAPPD_ENDPOINT': UNTAPPD_ENDPOINT,
                 'UNTAPPD_USERNAME': UNTAPPD_USERNAME}
    url = urlparse.urlparse(url)

    # Always append the client id and secret in addition to qs.
    query_dict = dict(urlparse.parse_qsl(url.query)) if url.query else {}
    query_dict.update({
        'client_id': UNTAPPD_CLIENT_ID,
        'client_secret': UNTAPPD_CLIENT_SECRET,
    })
    query_dict.update((k, v) for k, v in qs.items())
    query_string = urllib.urlencode([(k, v) for k, v in query_dict.items()
                                     if v is not None])
    return urlparse.urlunparse((url.scheme, url.netloc, url.path, url.params,
                                query_string, ''))


resp = requests.get(
    _url('%(UNTAPPD_ENDPOINT)s/user/checkins/%(UNTAPPD_USERNAME)s', limit=50))

while (resp.status_code == 200):
    data = resp.json()
    items = data['response']['checkins']['items']

    if not items:  # Are we out of data?
        es.indices.refresh(ES_INDEX)
        break

    # Convert string date to isoformat datetime.
    for i, item in enumerate(items):
        items[i]['created_at'] = dateutil.parser.parse(
           item['created_at']).isoformat()

    # pyelasticsearch did this for us but elasticsearch doesn't.
    body = []
    action = {'index': {'_index': ES_INDEX, '_type': ES_DOCTYPE}}
    for doc in items:
        body.append(action)
        body.append(doc)

    # Index into elasticsearch.
    es.bulk(body, ES_INDEX, ES_DOCTYPE)

    # Query next batch of checkins.
    resp = requests.get(_url(data['response']['pagination']['next_url']))
    print '.',
    sys.stdout.flush()


print
print "%d checkins imported!" % (
    es.count(ES_INDEX, ES_DOCTYPE)['count'])
print
print "Query your untappd checkins via elasticsearch at this URL:"
print "http://localhost:9200/%s/%s/" % (ES_INDEX, ES_DOCTYPE)
print
print "Or load the included charts in your browser for examples."
