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
import boto3
from urllib.parse import unquote_plus
import urllib
import time
import re
import os
from awsUtils import readTextFileFromS3, split_s3_path, insertParallelData, writeTextFileToS3

translate = boto3.client(service_name='translate', region_name='us-east-1', use_ssl=True)
a2i = boto3.client('sagemaker-a2i-runtime')

def lambda_handler(event, context):

    # describe the job to get details on the job completed.
    if event['detail']['humanLoopStatus'] == 'Completed':
        s3location = event['detail']['humanLoopOutput']['outputS3Uri']

    if s3location is None:
        return -1

    print("outputS3Uri :", s3location)

    ## Bucket to use
    bucketName, prefix = split_s3_path( s3location )
    # recreate the output text document, including post edits.
    tmsFile = json.loads(readTextFileFromS3( bucketName, prefix))
    inputContent = tmsFile['inputContent']
    rowcount = inputContent['rowCount']
    answerContent = tmsFile['humanAnswers'][0]['answerContent']
    translatedFileName = inputContent['keyName']
    editedContent = ''
    parallelDataInput = {
        'domain' : { 'S': 'Finance'},
        'sourceLanguageCode': { 'S': inputContent['sourceLanguageCode']},
        'targetLanguageCode' : { 'S': inputContent['targetLanguageCode']},
        'source' : None,
        'target': None
    }
    pattern = "<t>(.*?)</t>"
    for index in range(1, rowcount+1):
        if answerContent['addToCustom'+str(index)]['on']:
            ## insert into parallel data tableName
            #print(answerContent['translation'+str(index)])
            #print(answerContent['originalText'+str(index)])
            tagPatternTarget = re.search( pattern, answerContent['translation'+str(index)])
            tagPatternSource = re.search( pattern, answerContent['originalText'+str(index)])
            if tagPatternTarget is not None and tagPatternTarget is not None:
                ## extract phrases
                sourceTxt = tagPatternSource.group(1)
                targetTxt = tagPatternTarget.group(1)
                parallelDataInput['source'] = { 'S': sourceTxt}
                parallelDataInput['target'] = { 'S': targetTxt}
            else:
                parallelDataInput['source'] = { 'S': inputContent['translationPairs'][index-1]['originalText']}
                parallelDataInput['target'] = { 'S': answerContent['translation'+str(index)]}
            insertParallelData( 'translate_parallel_data', parallelDataInput)

        editedContent += (answerContent['translation'+str(index)].replace('<t>','').replace('</t>','') + " ")



    writeTextFileToS3( bucketName, 'edited/{0}'.format(translatedFileName), editedContent)
    print('Success')
    return 0
