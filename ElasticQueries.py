import json


def loadElasticQueries():
    with open('./ElasticQueries.json', 'r') as f:
        elasticQueries = json.load(f)
    return elasticQueries


elasticQueries = [q['query'] for q in loadElasticQueries()]
