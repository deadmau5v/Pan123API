import os
import time
from pprint import pprint

import requests
from dotenv import load_dotenv
import redis


class Pan123API:
    def __init__(self):
        self.clientID: str = ""
        self.clientSecret: str = ""
        self.BaseURL: str = ""
        self.RedisPassword: str = ""

        self.Authorization: dict = {}
        # 缓存
        self.Rds: redis.StrictRedis | None = None

        self.init()


    def init(self):
        """
        初始化
        :return: None
        """
        # 读取环境变量
        load_dotenv()
        self.clientID = os.getenv("clientID")
        self.clientSecret = os.getenv("clientSecret")
        self.BaseURL = os.getenv("BaseURL")
        self.RedisPassword = os.getenv("RedisPassword")

        self.Rds = redis.StrictRedis(host='localhost', port=6379, db=0, password=self.RedisPassword)

        if not self.Rds.exists("Authorization" or not self.Rds.exists("expiredAt")):
            self.Rds.set("Authorization", "")
            self.Rds.set("expiredAt", "")

        self.get_authorization()

    def get_authorization(self, skip_cache=False):
        """
        获取 Authorization 请求头
        :param skip_cache: 是否跳过缓存
        :return: 请求头
        """

        # 跳过缓存
        if skip_cache:
            self.Rds.delete("Authorization")
            self.Rds.delete("expiredAt")
            self.Rds.set("Authorization", "")
            self.Rds.set("expiredAt", "")

        expiredAt = self.Rds.get("expiredAt").decode("utf-8")
        if expiredAt != "":
            # 对比现在的时间 没过期就返回
            expiredAtTime = time.mktime(time.strptime(expiredAt, "%Y-%m-%dT%H:%M:%S+08:00"))
            now = time.time()
            if now < expiredAtTime:
                headers_ = {
                    "Authorization": f"{self.Rds.get('Authorization').decode('utf-8')}"
                }
                self.Authorization = headers_
                return headers_


        def get_access_token():
            """
            通过 clientID 和 clientSecret 获取 access_token
            :return:
            """
            api_ = self.BaseURL + "/api/v1/access_token"

            # print(api, clientID, clientSecret)
            headers__ = {
                "Platform": "open_platform"
            }
            res_ = requests.post(api_, headers=headers__, data={
                "clientID": self.clientID,
                "clientSecret": self.clientSecret
            })

            return res_.json()

        access_data = get_access_token()["data"]
        access_token = access_data["accessToken"]

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        self.Rds.set("Authorization", headers["Authorization"])
        self.Rds.set("expiredAt", access_data["expiredAt"])

        self.Authorization = headers
        return headers

    def default_headers(self):
        return {
            "Authorization": self.Authorization["Authorization"],
            "Platform": "open_platform"
        }

    def get_file_list(self, parentFileId: int=0, limit:int=100, searchData: str | None=None, searchMode: int=0, lastFileId: int | None=None):
        """
        获取文件列表
        :param parentFileId: 根目录ID 默认为0  (必填)
        :param limit: 页大小 默认为100  (必填)
        :param searchData: 是否搜索 如果搜索忽略 parentID
        :param searchMode: 搜索模式 默认为0模糊 1精准
        :param lastFileId: 上一页最后一个文件ID 翻页时需要
        :return:
        """
        api = self.BaseURL + "/api/v2/file/list"
        headers = self.default_headers()
        data = {
            "parentFileId": parentFileId,
            "limit": limit,
        }

        if lastFileId:
            data["lastFileId"] = lastFileId
        if searchData:
            data["searchData"] = searchData
            data["searchMode"] = searchMode

        res = requests.get(api, headers=headers, params=data)

        return res.json()

if __name__ == '__main__':
    pan = Pan123API()
    pprint(pan.get_file_list())
