###
 # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 # SPDX-License-Identifier: MIT-0
 #
 # Permission is hereby granted, free of charge, to any person obtaining a copy of this
 # software and associated documentation files (the "Software"), to deal in the Software
 # without restriction, including without limitation the rights to use, copy, modify,
 # merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
 # permit persons to whom the Software is furnished to do so.
 #
 # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
 # INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
 # PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 # HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 # OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 # SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 # Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
#   SPDX-License-Identifier: MIT
######
import json
import os
import xml.etree.ElementTree as et
from awsUtils import AwsUtils

# Get the service resources
aws_utils = AwsUtils(os.environ['AWS_REGION'])
parallelDataName = os.environ['PARALLEL_DATA_NAME']


def lambda_handler(event, context):

    # Read customization data written to DynamoDB
    table_name = os.environ.get('CUSTOM_DATA_TABLE_NAME', 'translate_parallel_data')

    # Transpose customization data to parallel data format
    parallel_data = to_tmx_format(aws_utils.read_customization_data(table_name))

    # Write transposed data to S3 parallel data location
    bucket = os.environ.get('PARALLEL_DATA_LOCATION')
    object_key = 'paralleldata/parallel_data.xml'

    aws_utils.write_s3_file(bucket, object_key, parallel_data, "text/xml")

    aws_utils.start_parallel_data_job( parallelDataName, "s3://" + bucket + "/" + object_key)


    return {
        'statusCode': 200,
        'body': json.dumps('Updated Parallel Data')
    }


def to_csv_format(data: list) -> str:
    languages = data[0].keys()
    output_text = ','.join(languages) + '\n'
    for row in data:
        output_text += ','.join(row.values()) + '\n'

    return output_text


def to_tsv_format(data: list) -> str:
    languages = data[0].keys()
    output_text = '\t'.join(languages) + '\n'
    for row in data:
        output_text += '\t'.join(row.values()) + '\n'

    return output_text


def to_tmx_format(data: list) -> str:
    root = et.Element('tmx')
    root.set('version', '1.4')
    header = et.SubElement(root, 'header')
    header.set('srclang', 'en')
    body = et.SubElement(root, 'body')

    for row in data:
        row_xml = et.SubElement(body, 'tu')
        row_item = et.SubElement(row_xml, 'tuv')
        row_item.set( 'xml:lang', row['sourceLanguageCode']['S'])
        row_seg = et.SubElement(row_item, 'seg')
        #print( row['source']['S'] )
        row_seg.text = row['source']['S']
        row_item1 = et.SubElement(row_xml, 'tuv')
        row_item1.set('xml:lang',  row['targetLanguageCode']['S'])
        row_seg1 = et.SubElement(row_item1, 'seg')
        row_seg1.text = row['target']['S']
        #print( row['target']['S'] )
    # Write parallel data to temporary file
    #fp = open('/tmp/parallel_data_tmp.xml', 'bw')
    #tree = et.ElementTree(root)
    xmlstr = et.tostring(root, encoding='UTF-8',  method='xml').decode()
    xmlHeader = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
    print( xmlHeader+str(xmlstr) )
    return xmlHeader+str(xmlstr)

def dynamodb_format_to_cannonical(dynamo_data: list) -> list:
    output_list = []
    for item in dynamo_data:
        new_item = {
            item['sourceLanguageCode']: item['source'],
            item['targetLanguageCode']: item['target']
        }
        output_list.append(new_item)

    return output_list
