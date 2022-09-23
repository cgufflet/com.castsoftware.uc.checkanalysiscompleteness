"""
REST API helpers to access to determinator (behind extend)

Author: CGU - September 2021
"""
import json
import os
import csv
import html

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


def get_keywords_per_extension_id(extension_id, aip_version):
    """
    :keywords list of keywords
    :return: 201 if created
    """
    conn = HTTPSConnection(EXTEND_HOSTNAME)
    apikey = os.getenv('EXTEND_API_KEY')

    headers = {'Content-Type': 'application/json', 'X-CAST-AIP' : aip_version, 'x-nuget-apikey' : apikey}
    conn.request('GET', EXTEND_API_URL + '/id/%s' % extension_id, headers=headers)
    response = conn.getresponse()
    if response.status != 200:
        print(response.status)
        return []

    encoding = response.info().get_content_charset('utf-8')
    json_data = json.loads(response.read().decode(encoding))

    conn.close()
    return json_data


def put_or_delete_keyword_to_extension(keyword, aip_version, extension_id, putOperation = True):
    """
    :keyword to map or to unmap to an extension id with a minimal version of AIP
    : aip_version minimal version of AIP
    :return: 201 if created
    """
    conn = HTTPSConnection(EXTEND_HOSTNAME)
    apikey = os.getenv('EXTEND_API_KEY')

    headers = {'Content-Type': 'application/json', 'x-nuget-apikey' : apikey}
    if putOperation:
        conn.request('PUT', EXTEND_API_URL + '/id/%s/technology/%s' % (extension_id, keyword), headers=headers)
    else:
        conn.request('DELETE', EXTEND_API_URL + '/id/%s/technology/%s' % (extension_id, keyword), headers=headers)

    response = conn.getresponse()
    if response.status != 200:
        print(response.status)
        return []

    encoding = response.info().get_content_charset('utf-8')
    json_data = json.loads(response.read().decode(encoding))

    conn.close()
    return json_data


def get_keyword_mappings_per_extension():
    """
        for each extension id, get list of keywords mapped in deternminator
    """
    extension_list = ['com.castsoftware.aip',
                      'com.castsoftware.android',
                      'com.castsoftware.angularjs',
                      'com.castsoftware.architecture',
                      'com.castsoftware.asp',
                      'com.castsoftware.awsdotnet',
                      'com.castsoftware.awsjava',
                      'com.castsoftware.azure.dotnet',
                      'com.castsoftware.azure.java',
                      'com.castsoftware.birt',
                      'com.castsoftware.bpel',
                      'com.castsoftware.camel',
                      'com.castsoftware.cloudconfig',
                      'com.castsoftware.cpp',
                      'com.castsoftware.dotnet',
                      'com.castsoftware.dotnet.dapper',
                      'com.castsoftware.dotnet.nhibernate',
                      'com.castsoftware.dotnet.service',
                      'com.castsoftware.dotnetweb',
                      'com.castsoftware.ead4j',
                      'com.castsoftware.egl',
                      'com.castsoftware.ejb',
                      'com.castsoftware.entity',
                      'com.castsoftware.flex',
                      'com.castsoftware.fortran',
                      'com.castsoftware.grpcjava',
                      'com.castsoftware.gwt',
                      'com.castsoftware.html5',
                      'com.castsoftware.ibatis',
                      'com.castsoftware.ios',
                      'com.castsoftware.java.service',
                      'com.castsoftware.java2program',
                      'com.castsoftware.jaxrs',
                      'com.castsoftware.jaxws',
                      'com.castsoftware.jee',
                      'com.castsoftware.jeerules',
                      'com.castsoftware.jquery',
                      'com.castsoftware.kotlin',
                      'com.castsoftware.mqe',
                      'com.castsoftware.nodejs',
                      'com.castsoftware.nosqldotnet',
                      'com.castsoftware.nosqljava',
                      'com.castsoftware.objectivec',
                      'com.castsoftware.php',
                      'com.castsoftware.pl1',
                      'com.castsoftware.python',
                      'com.castsoftware.reactjs',
                      'com.castsoftware.rpg',
                      'com.castsoftware.sap.hybris',
                      'com.castsoftware.sapui5',
                      'com.castsoftware.shell',
                      'com.castsoftware.springbatch',
                      'com.castsoftware.springdata',
                      'com.castsoftware.springmvc',
                      'com.castsoftware.springsecurity',
                      'com.castsoftware.springwebflow',
                      'com.castsoftware.sqlanalyzer',
                      'com.castsoftware.struts',
                      'com.castsoftware.swift',
                      'com.castsoftware.swing',
                      'com.castsoftware.tibco',
                      'com.castsoftware.typescript',
                      'com.castsoftware.vuejs',
                      'com.castsoftware.wcf',
                      'com.castsoftware.wpf'
                    ]
    with open("keywords_per_extension.csv", 'w+', newline='', encoding='utf-8') as csvfile:
        field_names = ['extension',
                      'keywords']
        count = 0
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(field_names)

        for extension in extension_list:
            determinator_response = get_keywords_per_extension_id(extension, '8.3.39')
            row = [extension, determinator_response]
            csvwriter.writerow(row)
            count += 1

        print('Exported #%d rows in %s' % (count, csvfile.name))
    csvfile.close()


if __name__ == "__main__":
    list_technos = ["Abap", "Activemq", "Ado.net", "Amazon mq", "Amazon sns", "Amazon sqs", "Android", "Angular", "Antlr",
     "Apache camel", "Apache hadoop", "Apache kafka", "Apache-camel", "Apachecxf", "Apachehttp", "Apachewink", "Apollo",
     "Ase tsql", "Asp", "Aspdotnet", "Aspdotnetcore", "Aspdotnetiframe", "Aspdotnetmvc", "Aspdotnetrazor", "Avro",
     "Aws cloudformation", "Aws s3", "Awsdotnet", "Awsjava", "Awslambda", "Awsnodejs", "Awspython", "Axios", "Axis",
     "Azuredotnet", "Azurejava", "Azurenodejs", "Azurepython", "Bash", "Birt", "Blueprint", "Bourneshell", "Bpel",
     "Businessobjects", "Cassandra", "Cast", "Cdi", "Cics", "Cobol", "Cobol as400", "Cobolvms", "Coldfusion",
     "Cosmosdb", "Couchbase", "Couchdb", "Couchdb-nano", "Cpp", "Csharp", "Cshell", "Css", "Dapper", "Datasafety",
     "Datastage", "Db2udb", "Db2zos", "Django", "Dotnet", "Dotnet2rest", "Dotnetinterop", "Dynamodb", "Ead4j", "Egl",
     "Ejb", "Elasticsearch", "Ember js", "Entity", "Enyim", "Express", "Flask", "Flex", "Fortify-js", "Fortran",
     "Functionpoint", "Gcos cobol", "Gradle", "Graphql", "Grpc", "Guava", "Gwt", "Hapi", "Haskell", "Hibernate",
     "Html5", "Ibm mq", "Ideal", "Ims", "Imsdb", "Informix", "Ingres", "Ios", "Jackson", "Jade", "Java",
     "Java-websocket", "Java2program", "Java2rest", "Javascript", "Jax-rpc", "Jax-rs", "Jaxrs", "Jaxws", "Jcl",
     "Jclcics", "Jee", "Jersey", "Jjwt", "Jms", "Jongo", "Jpa", "Jquery", "Jscript", "Jsf", "Jsp", "Kafka", "Knex",
     "Koa", "Kornshell", "Kotlin", "Kubernetes", "Laravel", "Linq", "Log4j", "Loopback", "Mariadb", "Marklogic",
     "Maven", "Memcached", "Microfocus cobol", "Mongo-sanitize", "Mongoclient", "Mongodb", "Mongoose", "Mqtt",
     "Ms tsql", "Msbuild", "Mustache", "Mybatis", "Mysql", "Natural", "Node-couchdb", "Node.js", "Nosqldotnet",
     "Nosqljava", "Nuget", "Objective-c", "Oracleforms", "Oraclereports", "Pacbase", "Peoplesoft", "Perl", "Php", "Pl1",
     "Plsql", "Postgresql", "Powerbuilder", "Powercenter", "Pro*c", "Pubsub", "Python", "Quality", "Querydsl",
     "Rabbitmq", "Rdl", "Rds", "React", "Reactivex", "Realm", "Redis", "Relay", "Resteasy", "Restify", "Retrofit",
     "Rpg", "Rpg(sql)", "Sails", "Sapui5", "Security", "Seneca", "Sequeslize", "Sh", "Shell", "Siebel", "Silverlight",
     "Snakeyaml", "Spring", "Spring jms", "Spring web flow", "Springapmq", "Springbatch", "Springdata",
     "Springintegration", "Springmvc", "Springsecurity", "Springweb", "Spymemcached", "Sqlalchemy", "Sqlite", "Sqr",
     "Struts", "Stxx", "Swift", "Swing", "Symfony", "Tcsh", "Tenex c shell", "Teradata", "Tibco", "Tiles", "Typescript",
     "Vb.net", "Vbscript", "Visualbasic", "Vue", "Vuex", "Wcf", "Winforms", "Wpf", "Wsdl", "Xamarin", "Xpdl",
     "Zookeeper", "Zsh"]

    """
    for row in programming_languages:
        determinator_response = get_extension_from_keywords([row], "8.3.39")
        #print(determinator_response)
        for determin in determinator_response.values():
            if not determin[0]['supported']:
                print(row + ',' + 'Not Supported')
    """

    """
    data = list(csv.reader(open('frameworksonly.csv'), delimiter=','))
    data[1:] = sorted(data[1:], key=lambda x: x[1])
    for row in data[1:]:
        determinator_response = get_extension_from_keywords([row[1]], "8.3.39")
        #print(determinator_response)
        for determin in determinator_response.values():
            print(row[0] + ',' + row[1] + ',' + str(determin[0]['supported']))

    """
    get_keyword_mappings_per_extension()
    #put_or_delete_keyword_to_extension('azuretypescript', '8.3.3', 'com.castsoftware.typescript')
    #put_or_delete_keyword_to_extension('nhibernate', '8.3.3', 'com.castsoftware.typescript', False)

    #put_or_delete_keyword_to_extension('azuredotnet', '8.3.3', 'com.castsoftware.azure.dotnet')
    #put_or_delete_keyword_to_extension('dapper', '8.3.3', 'com.castsoftware.dotnet.dapper')
    #put_or_delete_keyword_to_extension('aspdotnetcore', '8.3.3', 'com.castsoftware.dotnetweb')
    #put_or_delete_keyword_to_extension('nosqljava', '8.3.3', 'com.castsoftware.nosqljava')
    #put_or_delete_keyword_to_extension('nosqldotnet', '8.3.3', 'com.castsoftware.nosqldotnet')
    #put_or_delete_keyword_to_extension('java2program', '8.3.3', 'com.castsoftware.java2program')
    #put_or_delete_keyword_to_extension('pro*c', '8.3.3', 'com.castsoftware.cpp')
    #put_or_delete_keyword_to_extension('kafka', '8.3.3', 'com.castsoftware.mqe')
    #put_or_delete_keyword_to_extension('sqlalchemy', '8.3.3', 'com.castsoftware.python')


    """
    put_or_delete_keyword_to_extension('azurejava', '8.3.3', 'com.castsoftware.azure.java')
    put_or_delete_keyword_to_extension('azurenodejs', '8.3.3', 'com.castsoftware.nodejs')
    put_or_delete_keyword_to_extension('dotnet2rest', '8.3.3', 'com.castsoftware.dotnet.service')
    """
    for row in list_technos:
        determinator_response = get_extension_from_keywords([row], "8.3.39")
        #print(determinator_response)
        for determin in determinator_response.values():
            if not determin[0]['supported']:
                print(row)
            #print(row[0] + ',' + row[0] + ',' + str(determin[0]['supported']))








