#!/bin/env python
#coding:utf-8
#Author:WineeJam @2015-12-24
#modify: 2016-01-04


import json,os,requests,sys,platform
from lxml import etree

reload(sys)
sys.setdefaultencoding('utf-8')


class get_ss_info():
    def __init__(self,url,file):
        self.url = url
        self.file = file

    def get_source(self):
        r = requests.get(self.url, timeout = 3)
        r.encoding = 'utf-8'
        html = r.text
        return html

    def get_data(self):
        content = []
        html = self.get_source()
        selector = etree.HTML(html)
        for i in range(1,4):
            xpath_re = "//*[@id='free']/div/div[2]/div[%s]/h4/text()"%i
            tmp = selector.xpath(xpath_re)
            content.append(self.get_info(tmp))
        return content

    def get_info(self,data):
        result = []
        for i in range(0,4):
            result.append(data[i].split(":")[-1])
        return result

    def tojson(self,data):
        d = dict(server=data[0],server_port=int(data[1]),password=data[2],method=data[3])
        return d

    def getSSinfo(self):
        sslist = self.get_data()
        best_host = self.keep_a_best(sslist)
        for ss in sslist:
            if best_host in ss:
                ssinfo = self.tojson(ss)
        self.join_config_json(ssinfo)
        print "setting config.json succ. restart Shadowsocks now..."
        self.restart_ss()

    def restart_ss(self):
        stopcmd = 'taskkill /F /IM "Shadowsocks.exe"'
        ss_path = os.path.dirname(__file__) + os.sep + "Shadowsocks.exe"
        # ss_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + "Shadowsocks.exe"
        startcmd = 'cmd.exe /C start "" "%s"'%ss_path
        os.system(stopcmd)
        os.system(startcmd)

    def join_config_json(self,data):
        with open(self.file) as f:
            content = f.read()
        json_content = json.loads(content)
        tmp = json_content["configs"].pop()
        json_content["configs"].append(data)
        with open(self.file,"w") as f:
            f.write(json.dumps(json_content,sort_keys=True,indent=1))

    def keep_a_best(self,data):
        delays = []
        for each in data:
            ip = each[0]
            tmp = {}
            tmp['server'] = ip
            tmp['delay']=self.test_ping(ip)
            delays.append(tmp)
        delays_sorted = sorted(delays,key = lambda x:x['delay'])
        return delays_sorted[0]["server"]

    def test_ping(self,ip):
        sys_info = platform.system()
        if sys_info == "Linux":
            cmd = "ping -c 5 -i.01 -W 1 -s 1024 -f %s"%str(ip)
            cmd_out = commands.getoutput(cmd)
            tmp = cmd_out.split("\n")[-2:]
            try:
                loss = int(tmp[0].split(',')[2].split()[0].replace("%",""))
                delay = int(tmp[-1].split("/")[4].split(".")[0])
            except IndexError:
                cmd_out = [100,0]
            cmd_out = [loss,delay]
        elif sys_info == "Windows":
            cmd = "chcp 437  && ping -n 5 -w 500 -l 1024 %s"%str(ip)
            cmd_out = os.popen(cmd).read()
            tmp = cmd_out.split("\n")[-4:]
            try:
                loss = int(tmp[0].split("(")[1].split()[0].replace("%",""))
                delay = int(tmp[-2].split()[-1].replace("ms",""))
            except IndexError:
                cmd_out = [100,0]
            cmd_out = [loss,delay]
        return cmd_out


url = "http://www.ishadowsocks.com"
config_file = "gui-config.json"
if not os.path.exists(config_file):
    print "%s not found."%config_file
    sys.exit()
ss = get_ss_info(url,config_file)
ss.getSSinfo()

