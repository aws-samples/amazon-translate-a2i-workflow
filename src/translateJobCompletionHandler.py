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
import os
from awsUtils import readTextFileFromS3, split_s3_path
from sentenceSegmenter import split_sentences

translate = boto3.client(service_name='translate', region_name='us-east-1', use_ssl=True)
a2i = boto3.client('sagemaker-a2i-runtime')
ssm = boto3.client('ssm')


parameterName = unquote_plus(os.environ['SSMParameterName'])

def get_parameter( parameter_name):
    response = ssm.get_parameter(Name=parameter_name)
    parameter_value = json.loads(response['Parameter']['Value'])
    return parameter_value

def lambda_handler(event, context):

    # Get the JobId from the event
    jobId = event['detail']['jobId']
    jobStatus = event['detail']['jobStatus']
    waitingJobStatus = ['SUBMITTED', 'IN_PROGRESS']
    completedJobStatus = ['COMPLETED', 'COMPLETED_WITH_ERROR']
    print('Job Status :', jobStatus)
    if jobStatus in waitingJobStatus:
        return {
            'statusCode': 200,
            'status': jobStatus
    }

    if jobStatus not in completedJobStatus:
       return {
            'statusCode': 500,
            'status': jobStatus
    }

    # describe the job to get details on the job completed.
    describeResponse = translate.describe_text_translation_job( JobId=jobId)
    #jobStatus = describeResponse['TextTranslationJobProperties']['JobStatus']

    outputDataPrefix = describeResponse['TextTranslationJobProperties']['OutputDataConfig']['S3Uri']
    print("outputDataPrefix :", outputDataPrefix)
    detailsFilePrefix = outputDataPrefix + "details/es.auxiliary-translation-details.json"
    print("detailsFilePrefix :", detailsFilePrefix)

    outBucketName, outputKey = split_s3_path(detailsFilePrefix)
    flowDefnARN = get_parameter( parameterName)['flow_definition_arn']

    ## Bucket to use

    content_object = readTextFileFromS3( outBucketName, outputKey)
    json_content = json.loads(content_object)

    inputDataPrefix = json_content['inputDataPrefix']

    sourceBucketName, sKey = split_s3_path(inputDataPrefix)
    outBucketName, outputKey = split_s3_path(outputDataPrefix)

    ## List objects within a given prefix
    for translateDetail in json_content['details']:
      print( 'Source file: ', translateDetail['sourceFile'], ' Target file: ', translateDetail['targetFile'])
      sourceContent = readTextFileFromS3(sourceBucketName, sKey  + translateDetail['sourceFile'])
      targetContent = readTextFileFromS3(outBucketName, outputKey + translateDetail['targetFile'])
      ## use sentence segmenter and create Translate Pair & create Human loop
      sourceSentences = split_sentences(sourceContent, 'english')
      targetSentences = split_sentences(targetContent, 'spanish')

      rowCount = 0
      # Create the human loop input JSON object
      humanLoopInput = {
          'SourceLanguage' : 'english',
          'TargetLanguage' : 'spanish',
          'sourceLanguageCode':'en',
          'targetLanguageCode' : 'es',
          'translationPairs' : [],
          'rowCount': 0,
          'bucketName': outBucketName,
          'keyName': translateDetail['targetFile']
      }

      print('Splitting file and performing translation')
      sentenceIndex = 0
      # split the body by period to get individual sentences
      for sentence in sourceSentences:
        if len(sentence.lstrip()) > 0:
            translationPair = {
                                'originalText': sentence,
                                'translation': targetSentences[sentenceIndex]
                              }
            humanLoopInput['translationPairs'].append(translationPair)
            sentenceIndex+=1

      humanLoopInput['rowCount'] = sentenceIndex
      humanLoopName = 'Translate-HumanLoop-Text' + str(int(round(time.time() * 1000)))
      print('Starting human loop - ' + humanLoopName)
      response = a2i.start_human_loop(
                                HumanLoopName=humanLoopName,
                                FlowDefinitionArn= flowDefnARN,
                                HumanLoopInput={
                                    'InputContent': json.dumps(humanLoopInput)
                                    }
                                )

    print('Success')
    return {
         'statusCode': 200,
         'status': jobStatus
    }
