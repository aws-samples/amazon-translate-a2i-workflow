import boto3

_s3Client = None

_dynamoDBClient = None

def getS3Client():
    global _s3Client
    if( _s3Client is None):
        _s3Client = boto3.client('s3')
    return _s3Client

def getDynamoDBClient():
    global _dynamoDBClient
    if( _dynamoDBClient is None):
        _dynamoDBClient = boto3.client('dynamodb')
    return _dynamoDBClient

def readTextFileFromS3( bucketName, prefix ):
    s3Client = getS3Client()
    print( "reading from bucket ", bucketName, " key ", prefix)
    data = s3Client.get_object(Bucket=bucketName, Key=prefix)
    contents = data['Body'].read()
    return contents.decode("utf-8")

def writeTextFileToS3( bucketName, prefix, content):
    s3Client = getS3Client()
    print( "writeTextFileToS3 from bucket ", bucketName, " key ", prefix)
    # save the file.
    s3Client.put_object(Bucket=bucketName,
                          Key=prefix,
                          Body=content.encode('utf-8'))
    return 1



def insertParallelData( tableName, data):
    dynamoDBClient = getDynamoDBClient()
    print( "insertParallelData ", tableName)
    response = dynamoDBClient.put_item(TableName=tableName, Item=data)
    return 1

def split_s3_path(s3_path):
    path_parts = s3_path.replace("s3://","").split("/")
    bucket = path_parts.pop(0)
    key = "/".join(path_parts)
    return bucket, key


class AwsUtils:

    def __init__(self, region=None):
        self.region = region
        if self.region:
            self._s3_client = boto3.client('s3', region_name=self.region)
            self._dynamodb_client = boto3.client('dynamodb', region_name=self.region)
            self._translate_client = boto3.client(service_name='translate', region_name=self.region,
                                           use_ssl=True)

        else:
            self._s3_client = boto3.client('s3')
            self._dynamodb_client = boto3.client('dynamodb')
            self._translate_client = boto3.client('translate', use_ssl=True)

    @staticmethod
    def split_s3_path(s3_path: str) -> tuple:
        path_parts = s3_path.replace("s3://", "").split("/")
        bucket = path_parts.pop(0)
        key = "/".join(path_parts)
        return bucket, key

    @staticmethod
    def build_s3_uri(*segments) -> str:
        return "s3://" + '/'.join(segments) + '/'

    def read_s3_file(self, bucketName: str, prefix: str, verbose=False) -> str:
        if verbose:
            print( "reading from bucket ", bucketName, " key ", prefix)
        data = self._s3_client.get_object(Bucket=bucketName, Key=prefix)
        contents = data['Body'].read()
        return contents.decode("utf-8")

    def write_s3_file(self, bucketName: str, prefix: str, content: str, contentType: str,verbose=False):
        if verbose:
            print( "writeTextFileToS3 from bucket ", bucketName, " key ", prefix)
        # save the file.
        self._s3_client.put_object(Bucket=bucketName,
                                   Key=prefix,
                                   Body=content,
                                   ContentType=contentType)
        return True

    def write_customization_data(self, table_name: str, data: str, verbose=False):
        if verbose:
            print("Write Customization Data", table_name)
        response = self._dynamodb_client.put_item(TableName=table_name, Item=data)
        return True

    def read_customization_data(self, table_name: str, verbose=False) -> list:
        if verbose:
            print("Read Customization Data", table_name)
        response = self._dynamodb_client.scan(TableName=table_name)
        return response['Items']

    def start_translate_batch_job(self, jobName: str, batchInputS3URI: str, batchOutputS3URI: str,
                                  data_role_arn: str, parallelDataNames: list,source_lang: str ='en',
                                  target_lang: list = ['es']):
        if parallelDataNames is None:
            return self._translate_client.start_text_translation_job(
                JobName=jobName,
                InputDataConfig={
                    "S3Uri": batchInputS3URI,
                    "ContentType": "text/plain"
                },
                OutputDataConfig={
                    "S3Uri": batchOutputS3URI,
                },
                DataAccessRoleArn=data_role_arn,
                SourceLanguageCode=source_lang,
                TargetLanguageCodes=target_lang)
        else:
            return self._translate_client.start_text_translation_job(
                JobName=jobName,
                InputDataConfig={
                    "S3Uri": batchInputS3URI,
                    "ContentType": "text/plain"
                },
                OutputDataConfig={
                    "S3Uri": batchOutputS3URI,
                },
                DataAccessRoleArn=data_role_arn,
                SourceLanguageCode=source_lang,
                TargetLanguageCodes=target_lang,
                ParallelDataNames=parallelDataNames)


    def checkParallelDataJob(self, jobName: str):
        response = self._translate_client.list_parallel_data()
        parallelDataExists = False;
        for parallelData in response['ParallelDataPropertiesList']:
            if parallelData['Name'] == jobName and parallelData['Status'] == 'ACTIVE':
                parallelDataExists=True
                break
        return parallelDataExists

    def start_parallel_data_job(self, jobName: str, parallelDataS3Uri: str):
        response = self._translate_client.list_parallel_data()
        createParallelData = True;
        for parallelData in response['ParallelDataPropertiesList']:
            if parallelData['Name'] == jobName:
                createParallelData=False
                break
        if createParallelData:
            return self._translate_client.create_parallel_data(
                Name=jobName,
                Description='Translate parallel data job',
                ParallelDataConfig={
                    'S3Uri': parallelDataS3Uri,
                    'Format': 'TMX'
                }
                )
        else:
            return self._translate_client.update_parallel_data(
                Name=jobName,
                Description='Translate parallel data job',
                ParallelDataConfig={
                    'S3Uri': parallelDataS3Uri,
                    'Format': 'TMX'
                }
                )
