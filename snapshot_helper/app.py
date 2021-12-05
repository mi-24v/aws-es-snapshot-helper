import os

import requests
from requests_aws4auth import AWS4Auth


def lambda_handler(event, context):
    host = event["domain_url"]  # include https:// and trailing /
    action = event["action"]
    repository_name = event["repo_name"]
    access_key = os.environ["AWS_ACCESS_KEY_ID"]
    secret_key = os.environ["AWS_SECRET_ACCESS_KEY"]
    region = os.environ["AWS_REGION"]
    service = 'es'
    session_token = os.environ["AWS_SESSION_TOKEN"]
    awsauth = AWS4Auth(access_key, secret_key, region, service, session_token=session_token)
    executor = SnapShotAction(host, region, repository_name, awsauth)
    if action == "register_repository":
        executor.register_repository(event["register_repository_role"], os.environ["SNAPSHOT_BUCKET"])
    elif action == "take_snapshot":
        executor.take_snapshot(event["snapshot_name"])
    elif action == "delete_index":
        executor.delete_index(event["index_name"])
    elif action == "restore_snapshot_one_index":
        executor.restore_snapshot_one_index(event["snapshot_name"], event["index_name"])
    elif action == "restore_snapshot_all_index":
        executor.restore_snapshot_all_index(event["snapshot_name"])
    elif action == "restore_snapshot_in_fine_acl":
        executor.restore_snapshot_in_fine_acl(event["snapshot_name"])
    else:
        executor.check_all_snapshot()


class SnapShotAction:
    host: str
    region: str
    snapshot_repo_name: str
    awsauth: AWS4Auth

    def __init__(self, host, region, repo_name, auth):
        self.host = host
        self.region = region
        self.snapshot_repo_name = repo_name
        self.awsauth = auth

    # Register repository
    def register_repository(self, role_arn, bucket_name):
        path = '_snapshot/' + self.snapshot_repo_name  # the OpenSearch API endpoint
        url = self.host + path
        payload = {
            "type": "s3",
            "settings": {
                "bucket": bucket_name,
                "region": self.region,
                "role_arn": role_arn
            }
        }
        headers = {"Content-Type": "application/json"}
        r = requests.put(url, auth=self.awsauth, json=payload, headers=headers)
        print(r.status_code)
        print(r.text)

    # Take snapshot
    def take_snapshot(self, snapshot_name):
        path = '_snapshot/{}/{}'.format(self.snapshot_repo_name, snapshot_name)
        url = self.host + path

        r = requests.put(url, auth=self.awsauth)

        print(r.text)

    def check_all_snapshot(self):
        path = '_snapshot/{}/_all?pretty'.format(self.snapshot_repo_name)
        url = self.host + path

        r = requests.get(url, auth=self.awsauth)

        print(r.text)

    # Delete index
    def delete_index(self, index_name):
        url = self.host + index_name

        r = requests.delete(url, auth=self.awsauth)

        print(r.text)

    # Restore snapshot (all indices except Dashboards and fine-grained access control)
    def restore_snapshot_in_fine_acl(self, snapshot_name):
        path = '_snapshot/{}/{}/_restore'.format(self.snapshot_repo_name, snapshot_name)
        url = self.host + path
        payload = {
            "indices": "-.kibana*,-.opendistro_security",
            "include_global_state": False
        }
        headers = {"Content-Type": "application/json"}
        r = requests.post(url, auth=self.awsauth, json=payload, headers=headers)
        print(r.text)

    # Restore snapshot (all index)
    def restore_snapshot_all_index(self, snapshot_name):
        path = '_snapshot/{}/{}/_restore'.format(self.snapshot_repo_name, snapshot_name)
        url = self.host + path
        headers = {"Content-Type": "application/json"}
        r = requests.post(url, auth=self.awsauth, headers=headers)
        print(r.text)

    # Restore snapshot (one index)
    def restore_snapshot_one_index(self, snapshot_name, index_name):
        path = '_snapshot/{}/{}/_restore'.format(self.snapshot_repo_name, snapshot_name)
        url = self.host + path
        payload = {"indices": index_name}
        headers = {"Content-Type": "application/json"}
        r = requests.post(url, auth=self.awsauth, json=payload, headers=headers)
        print(r.text)
