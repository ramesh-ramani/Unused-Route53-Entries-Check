import os
import boto3
import subprocess
#from subprocess import os.popen
import slackweb
#from subprocess import os.popen
import socket



##Below lines will connect to the AWS Route53 Client##

lst = [<profile name>]


def sgcheck(account,client):

  ##Below lines will get the Hosted Zone Ids from the Account's Route 53 and put it in a List##
  zone_type=0
  sum_public=0
  sum_private=0
  zone_id_name_dict = {}
  cname_name_dict_public = {}
  cname_name_dict_private = {}
  pvt_hosted_zones=list()
  public_hosted_zones=list()
  dict=client.list_hosted_zones()
  #print(dict)
  dict_1=dict['HostedZones']
  hosted_zones=[i['Id'].split("/hostedzone/")[1] for i in dict_1]
  for zone in dict_1:
      try:
         if not (zone['Config']['PrivateZone']):
            tmp_lst=[zone['Id'].split('/')[2]],zone['Name']
            public_hosted_zones.append(tmp_lst)
         else:
            tmp_lst=[zone['Id'].split('/')[2]],zone['Name']
            pvt_hosted_zones.append(tmp_lst)
      except: continue

  #print(public_hosted_zones)

##Below Lines will take the Hosted Zones from the "hosted_zoned" list and get the resource Records for each Hosted Zone##
  paginator = client.get_paginator('list_resource_record_sets')
  print("****Unused Public Route 53 Records****")
  for i in public_hosted_zones:
    response = paginator.paginate(HostedZoneId=i[0][0])
    print(i[0][0],)
    for record_set in response:
        for j in record_set['ResourceRecordSets']:
          if j['Type'] == 'CNAME':
           try:
             for record in j['ResourceRecords']:
                try:
                   x=socket.gethostbyname_ex(j['Name'])
                except: x="NXDOMAIN"
                try:
                   y=socket.gethostbyname_ex(record['Value'])
                except: y="NXDOMAIN" 
                if ("NXDOMAIN" in x) and ("NXDOMAIN" in y):
                  sum_public=sum_public+1
                  print("NAME: ",j['Name'],"CNAME: ",record['Value'])
                  cname_name_dict[j['Name']]=record['Value']
           except: pass
          elif 'AliasTarget' in j:
                   try:
                      x=socket.gethostbyname_ex(j['Name'])
                   except: x="NXDOMAIN"
                   if "NXDOMAIN" in x:
                     sum_public=sum_public+1
                     print("NAME: ",j['Name'],"Alias: ",j['AliasTarget']['DNSName'])
                     cname_name_dict_public[j['Name']]=j['AliasTarget']['DNSName']

  print("****Unused Private Route 53 Records****")
  for i in pvt_hosted_zones:
    response = paginator.paginate(HostedZoneId=i[0][0])
    print(i[0][0],)
    for record_set in response:
        for j in record_set['ResourceRecordSets']:
          if j['Type'] == 'CNAME':
           try:
             for record in j['ResourceRecords']:
                try:
                   x=socket.gethostbyname_ex(j['Name'])
                except: x="NXDOMAIN"
                try:
                   y=socket.gethostbyname_ex(record['Value'])
                except: y="NXDOMAIN"
                if ("NXDOMAIN" in x) and ("NXDOMAIN" in y):
                  sum_private=sum_private+1
                  print("NAME: ",j['Name'],"CNAME: ",record['Value'])
                  cname_name_dict[j['Name']]=record['Value']
           except: pass
          elif 'AliasTarget' in j:
                   try:
                      x=socket.gethostbyname_ex(j['Name'])
                   except: x="NXDOMAIN"
                   if "NXDOMAIN" in x:
                     sum_private=sum_private+1
                     print("NAME: ",j['Name'],"Alias: ",j['AliasTarget']['DNSName'])
                     cname_name_dict_private[j['Name']]=j['AliasTarget']['DNSName']
                   else: continue 


##Returning the Sum and the Dictionary##

  return sum_public,sum_private,cname_name_dict_public,cname_name_dict_private


##Function Call to S3 which will take the Files Generated in the Main Function (with the invalid Resource Records in it and upload it to S3##

def s3_call(account):
  session = boto3.Session(profile_name=<profile name>,region_name='us-west-2')
  s3=session.client('s3')
  s3.upload_file(<text file>)


##Function Call to Slack which will print out to Slack the Account Name and the Number of Invalid Resource Records in that Account##

def slack_call(account,sum_public,sum_private,cname_name_dict_public,cname_name_dict_private):
     slack = slackweb.Slack(url=os.environ.get('channel url'))
     if sum_private==0:
        slack.notify(text="`Number of Private Unused Route-53 entries(URLs) in the` "+str(account)+" account = 0")
     elif sum_private!=0:
        slack.notify(text="`Number of Private Unused Route-53 entries(URLs) in the` "+str(account)+" account = "+str(sum_private))
     if sum_public==0:
        slack.notify(text="`Number of Public Unused Route-53 entries(URLs) in the` "+str(account)+" account = 0")
     elif sum_public!=0:
        slack.notify(text="`Number of Public Unused Route-53 entries(URLs) in the` "+str(account)+" account = "+str(sum_public))

##Main##

def lambda_handler(event, context):
   slack = slackweb.Slack(url=os.environ.get('channel'))
   slack.notify(text="*Summary of Unused Route53 Check Results:*")
   slack.notify(text="==================================")
   
   for i in lst:
      print("========",i,"========")
      session = boto3.Session(region_name='us-west-2')
      client = session.client('route53')
      sum_public,sum_private,cname_name_dict_public,cname_name_dict_private=sgcheck(i,client)
      slack_call(i,sum_public,sum_private,cname_name_dict_public,cname_name_dict_private)

