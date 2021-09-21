"""
REST API helpers to access to determinator (behind extend)

Author: CGU - September 2021
"""
import json

from http.client import HTTPSConnection, HTTPConnection

EXTEND_HOSTNAME = "extend.castsoftware.com"
EXTEND_API_URL = "/api/determinator"
protocol_V4 = 4

def get_extension_from_keywords(keywords, aip_version):
    """
    :keywords list of keywords
    :return: 201 if created
    """
    conn = HTTPSConnection(EXTEND_HOSTNAME)

    data = {"technologies": keywords, "protocol": protocol_V4}

    headers = {'Content-Type': 'application/json', 'X-CAST-AIP' : aip_version}
    payload = json.dumps(data)
    conn.request('POST', EXTEND_API_URL, payload, headers)
    response = conn.getresponse()
    if response.status != 200:
        print(response.status)
        print('Failed to fetch from extend : ', payload)
        return []

    encoding = response.info().get_content_charset('utf-8')
    json_data = json.loads(response.read().decode(encoding))

    conn.close()
    return json_data

if __name__ == "__main__":
    determinator_response = get_extension_from_keywords(["SQL"], "8.3.36")
    print(determinator_response)

