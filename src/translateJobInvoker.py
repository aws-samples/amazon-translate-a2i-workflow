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
from urllib.parse import unquote_plus
import os
from awsUtils import AwsUtils

from datetime import datetime
# Get the service resources
aws_utils = AwsUtils(os.environ['AWS_REGION'])


def lambda_handler(event, context):

    aws_utils = AwsUtils()
    data_access_role_arn = os.environ['BATCH_TRANSLATION_ROLE']
    batchInputS3URI =  os.environ['BATCH_INPUT_S3URI']
    batchOutputS3URI =  os.environ['BATCH_OUTPUT_S3URI']
    parallelDataName =  os.environ['PARALLEL_DATA_NAME']
    print(data_access_role_arn)

    now = datetime.now() # current date and time
    date_time = now.strftime("-%m%d%Y%H%M%S")
    jobName = "translateBatchJob" + date_time
    parallelDataNames = None

    if aws_utils.checkParallelDataJob( parallelDataName ):
        parallelDataNames = [parallelDataName]
    # initiate asyncrhonous batch translation job with translate client
    response = aws_utils.start_translate_batch_job( jobName, batchInputS3URI,
    batchOutputS3URI, data_access_role_arn, parallelDataNames )

    return {
        'statusCode': 200,
        'body': json.dumps('Initiated Translate Batch Job')
    }
