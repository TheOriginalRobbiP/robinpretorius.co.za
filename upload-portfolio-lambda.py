import boto3
import StringIO
import zipfile
import mimetypes

def lambda_handler(event, context):
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:eu-west-2:976290992126:deployPortfolioTopic')
    
    try:
        job = event.get("CodePipeline.job")
        
        location = {
            'bucketName': 'build.robinpretorius.co.za',
            'objectKey': 'portfoliobuild.zip'
        }
        
        if job:
            for artifact in job['data']['inputArtifacts']:
                if artifact['name'] == 'MyAppBuild':
                    location = artifact['location']['s3Location']
            
        print "Building portfolio from " + str(location)   
       
        s3 = boto3.resource('s3')
        
        portfolio_bucket = s3.Bucket('robinpretorius.co.za')
        build_bucket = s3.Bucket(location['bucketName'])
        
        portfolio_zip = StringIO.StringIO()
        build_bucket.download_fileobj(location['objectKey'], portfolio_zip)
        
        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                portfolio_bucket.upload_fileobj(obj, nm,
                ExtraArgs={'ContentType': mimetypes.guess_type(nm)[0]})
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')
        
        print "Jobs done!"
        topic.publish(Subject="Portfolio Deployed", Message = "Your portfolio has been deployed.")
        
        if job:
            codepipeline = boto3.client('codepipeline')
            codepipeline.put_job_success_result(jobId=job['id'])
    except:
        topic.publish(Subject="Portfolio Deploy Failed", Message="Whoopsyy, you broke something.")
        raise
        
    return 'Hello from Lambda'