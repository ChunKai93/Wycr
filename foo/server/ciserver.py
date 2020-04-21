#!/usr/bin/python3
import os
import json
import time


class Ciserver(object):
    _instance = None

    def __new__(cls, type, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, type):
        self.type = type
        self.group = None
        self.group_list = None
        self.group_name = ""
        self.api_branch = ""
        self.admin_branch = ""
        self.common_branch = ""
        self.cigroupfolder = ""
        self.backup_file = ""
        self.pto = ""
        self.pto_time = ""
        self.publish_time = ""

    def get_group_list(self):
        if self.group_list is not None:
            return self.group_list

        group_list = None
        try:
            cigroup_file = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + "/conf/cigroup_" + self.type + ".json"
            f = open(cigroup_file, "r")
            group_list = f.read()
            f.close()

            self.group_list = json.loads(group_list)
        except Exception as err:
            print(str(err.__traceback__.tb_lineno))
            print(err)

        return group_list

    def get_group(self, cigroupname):
        if self.group_list is None:
            self.get_group_list()

        self.group_name = cigroupname
        if cigroupname in self.group_list:
            self.group = self.group_list[cigroupname]
            if self.group_list[cigroupname]["folder"]["branch"] is not None:
                self.api_branch = self.group_list[cigroupname]["folder"]["branch"]["api"]
                self.admin_branch = self.group_list[cigroupname]["folder"]["branch"]["admin"]
                self.common_branch = self.group_list[cigroupname]["folder"]["branch"]["common"]
            if self.group_list[cigroupname]["cigroupfolder"] is not None:
                self.cigroupfolder = self.group_list[cigroupname]["cigroupfolder"]
            return self.group_list[cigroupname]

        return None

    def get_server_info(self, cigroupname):
        cigroup = self.get_group(cigroupname)
        if cigroup is None:
            return False, False, "没有这个cigroup"
        elif cigroup["server_type"] == "s":
            return "s", cigroup["server_index"], None
        elif cigroup["server_type"] == "g":
            return "g", cigroup["server_group"], None
        else:
            return False, False, "没有这个server_type,现只支持\"g\"和\"s\""

    def get_nginx(self, cigroupname):
        cigroup = self.get_group(cigroupname)
        if cigroup is None:
            return False, {}

        certificate = ""
        for listen in cigroup["nginx"]["listenlist"]:
            port = str(listen["port"])
            if listen["ssl"] is True:
                port += " ssl http2"
                certificate = '''   ssl_certificate %s%s;
    ssl_certificate_key %s%s;
''' % (listen["certificate"]["path"], listen["certificate"]["crt"], listen["certificate"]["path"],
       listen['certificate']['key'])

        api = '''server {
    listen %s;
    server_name %s;
%s    
    root /files/php/%s/%s/default/api;
    location / {
        index  index.php index.html index.htm;
        if (!-e $request_filename){
            rewrite  ^(.*)$  /index.php?s=/$1  last;
            break;
        }
    }

    location ~ \.php$ {
        fastcgi_pass 127.0.0.1:9000;
        fastcgi_index index.php;
        fastcgi_param HTTPS on;
        fastcgi_param  SCRIPT_FILENAME    $document_root$fastcgi_script_name;
        include        fastcgi_params;
        include fastcgi.conf;
    }
    
    location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$ {
        root /files/php/%s/%s/default/;
        access_log off;
        expires 30d;
    }
    
    location ~ .*\.(js|css)?$ {
        access_log off;
        expires 1h;
    }
    access_log  /usr/local/nginx/logs/%s_api_%s.log main;
}''' % (port, cigroup["nginx"]["servername"]["api"], certificate, self.type, cigroupname, self.type, cigroupname, self.type, cigroupname)

        admin = '''server {
    listen %s;
    server_name %s;
%s
    root /files/php/%s/%s/default/admin;
    location / {
        index  index.php index.html index.htm;
        if (!-e $request_filename){
            rewrite  ^(.*)$  /index.php?s=/$1  last;
            break;
        }
    }

    location ~ \.php$ {
        fastcgi_pass 127.0.0.1:9000;
        fastcgi_index index.php;
        fastcgi_param HTTPS on;
        fastcgi_param  SCRIPT_FILENAME    $document_root$fastcgi_script_name;
        include        fastcgi_params;
        include fastcgi.conf;
    }

    location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$ {
        root /files/php/%s/%s/default/;
        access_log off;
        expires 30d;
    }

    location ~ .*\.(js|css)?$ {
        access_log off;
        expires 1h;
    }
    access_log  /usr/local/nginx/logs/%s_admin_%s.log main;
}''' % (port, cigroup["nginx"]["servername"]["admin"], certificate, self.type, cigroupname, self.type, cigroupname, self.type, cigroupname)

        return True, {"api": api, "admin": admin}

    def save_cigroup(self, cigroupname):
        if self.group_list is None:
            self.get_group_list()

        if self.group is None:
            self.get_group(cigroupname)

        group = json.dumps(self.group, sort_keys=True, indent=4, separators=(',', ': '))

        self.group_list[cigroupname]["cigroupfolder"] = self.cigroupfolder
        self.group_list[cigroupname]["folder"]["last_backup_file"] = self.group["folder"]["backup_file"]
        self.group_list[cigroupname]["folder"]["backup_file"] = self.backup_file
        self.group_list[cigroupname]["folder"]["pto"] = self.pto
        self.group_list[cigroupname]["folder"]["pto_time"] = self.pto_time
        self.group_list[cigroupname]["folder"]["publish_time"] = self.publish_time
        grouplist = json.dumps(self.group_list, sort_keys=True, indent=4, separators=(',', ': '))

        try:
            cigroup_file = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + "/conf/cigroup_" + self.type + ".json"
            f = open(cigroup_file, "w")
            f.write(grouplist)
            f.close()

            time_key = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
            distserverFile = '/files/sh/upload/backup_files/json/backup_' + cigroupname + '_' + time_key + '.json'
            f = open(distserverFile, 'w')
            f.write(group)
            f.close()
        except Exception as err:
            print("\033[1;35m保存数据失败：\033[0m")
            print(err)
