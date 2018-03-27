#!/home/longen/.pyenv/shims/python
# -*- coding:utf-8 -*-
import time
import json
import requests

from redis import Redis
from toolkit.monitors import Service

api_host = "http://192.168.200.34:8080"

redis_host = "192.168.200.150"

PROJECT = "Jay-Cluster"


class RancherMonitor(Service):

    def main(self):
        services = self.get_service(self.get_project_id(PROJECT))
        spiders = [data["name"].replace("-spider", "") for data in services["data"] if data["name"].endswith("spider")]
        redis_conn = Redis(host=redis_host)
        keys = set(key.decode("utf-8").split(":")[0].replace("_", "-") for key in redis_conn.keys("*item:queue"))
        for spider in keys:
            self.logger.debug("Activate %s. " % spider, end="")
            self.run({"project": PROJECT, "service": spider, "action": "activate"})
        time.sleep(5)
        keys2 = set(key.decode("utf-8").split(":")[0].replace("_", "-") for key in redis_conn.keys("*item:queue"))
        effect_keys = keys.union(keys2)
        for spider in (set(spiders)-effect_keys):
            self.logger.debug("Deactivate %s. " % spider, end="")
            self.run({"project": PROJECT, "service": spider, "action": "deactivate"})

    def get_project_id(self, project_name):
        """
        获取project_id
        :return:
        """
        resp = requests.get("%s/v2-beta/projects?all=true&limit=-1&sort=name" % api_host)
        project_env = json.loads(resp.text)
        for data in project_env["data"]:
            if data["name"].lower().count(project_name.lower()):
                project = data
                return project["id"]

    def get_service(self, project_id):
        """
        获取服务环境信息
        :param project_id:
        :return:
        """
        resp = requests.get("%s/v2-beta/projects/%s/services?limit=-1&sort=name" % (api_host, project_id))
        return json.loads(resp.text)

    def run(self, args):
        """
        提供project, service, action，执行api命令
        :param args:
        :return:
        """
        project_name, service_name, action_name = args["project"], args["service"], args["action"]
        project_id = self.get_project_id(project_name)
        if project_id:
            service_env = self.get_service(project_id)
            services = []
            for data in service_env["data"]:
                if data["name"].lower().count(service_name.lower()):
                    services.append(data)

            for service in services:
                action = service["actions"].get(action_name)
                if action:
                    self.logger.debug(
                        "API response code: %s. " % requests.post(
                            action, json={"rollingRestartStrategy": {}}).status_code)
                else:
                    self.logger.info(
                        "Cannot process %s %s! It have %sed perhaps. " % (service_name, action_name, action_name))
            else:
                self.logger.info("Cannot find service named %s! " % service_name)
        else:
            self.logger.info("Cannot find project named %s! " % project_name)


if __name__ == "__main__":
    rm = RancherMonitor()
    rm.main()