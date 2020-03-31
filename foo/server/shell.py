#!/usr/bin/python3
import os
import paramiko
import time
from foo.server import server, ciserver


class Shell(object):
    _instance = None

    def __new__(cls, type, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, type):
        self.srv = server.Server()
        self.csrv = ciserver.Ciserver(type)
        self.type = type
        self.group = ""
        self.server_list = []
        self.nginx_api = ""
        self.nginx_admin = ""
        self.normal_server_list = []
        self.sftp_status_list = []
        self.code_timestamp = ""
        self.codepath = ""

    def get_code_timestamp(self):
        if self.code_timestamp == "":
            ct = time.time()
            local_time = time.localtime(ct)
            data_head = str(time.strftime("%Y%m%d%H%M%S", local_time))
            data_secs = (ct - int(ct)) * 1000
            self.code_timestamp = data_head + str("%03d" % data_secs)
        return self.code_timestamp

    def set_group(self, group_name, server_list):
        self.group = group_name
        self.server_list = server_list

    def set_nginx(self, nginx):
        self.nginx_api = nginx["api"]
        self.nginx_admin = nginx["admin"]

    def push_nginx(self):
        if self.nginx_api == "" or self.nginx_admin == "":
            print("\033[1;31m生成nginx配置失败\033[0m")
            return False

        try:
            api_file = "/tmp/tmp_nginx_api.conf"
            f = open(api_file, "w")
            f.write(self.nginx_api)
            f.close()

            admin_file = "/tmp/tmp_nginx_a.conf"
            f = open(admin_file, "w")
            f.write(self.nginx_admin)
            f.close()
        except Exception as err:
            print(err)
            return False

        to_api_file = '/usr/local/nginx/conf/conf.d/tmp_nginx_api.conf'
        to_admin_file = '/usr/local/nginx/conf/conf.d/tmp_nginx_a.conf'

        self.__sftp_push(api_file, to_api_file)
        for list in self.sftp_status_list:
            if list["status"]:
                msg = "服务器host:\033[1;32m" + list["server"]["host"] + ":" + str(
                    list["server"]["port"]) + "\033[0m,sftp (from:" + api_file + ",to:" + to_api_file + ") 发送成功"
            else:
                msg = "服务器host:\033[1;32m" + list["server"]["host"] + ":" + str(
                    list["server"]["port"]) + "\033[0m,sftp (from:" + api_file + ",to:" + to_api_file + ") 发送失败"
            print(msg)
        self.__sftp_push(admin_file, to_admin_file)
        for list in self.sftp_status_list:
            if list["status"]:
                msg = "服务器host:\033[1;32m" + list["server"]["host"] + ":" + str(
                    list["server"]["port"]) + "\033[0m,sftp (from:" + admin_file + ",to:" + to_admin_file + ") 发送成功"
            else:
                msg = "服务器host:\033[1;32m" + list["server"]["host"] + ":" + str(
                    list["server"]["port"]) + "\033[0m,sftp (from:" + admin_file + ",to:" + to_admin_file + ") 发送失败"
            print(msg)
        return True

    def save_nginx(self):
        if self.csrv.group_name == "":
            return False, "cigroup为空"

        cmd = "mv /usr/local/nginx/conf/conf.d/tmp_nginx_a.conf /usr/local/nginx/conf/conf.d/" + self.csrv.group_name + "_a.conf"
        cmd += " && mv /usr/local/nginx/conf/conf.d/tmp_nginx_api.conf /usr/local/nginx/conf/conf.d/" + self.csrv.group_name + "_api.conf"
        cmd += " && service nginx reload"
        result_list = self.__cmd(cmd)
        for result in result_list:
            if not result["status"]:
                return False, result["host"] + ":" + result["port"] + ":" + result["msg"]["info"]

        return True, ""

    def check_nginx(self):
        cmd = "service nginx configtest"
        result_list = self.__cmd(cmd)
        for result in result_list:
            if result["status"]:
                pstr = "----------------------------------------------------------\n"
                if "successful" in result["msg"]["info"]:
                    pstr += "服务器host:\033[1;32m" + str(result["msg"]["host"]) + ":" + str(
                        result["msg"]["port"]) + "\033[0m,测试命令执行成功\n"
                    pstr += '\033[1;32mnginx配置正确\033[0m'
                    print(pstr)
                else:
                    pstr += "服务器host:\033[1;32m" + str(result["msg"]["host"]) + ":" + str(
                        result["msg"]["port"]) + "\033[0m,测试命令执行成功\n"
                    pstr += '\033[1;35m但nginx配置不正确\033[0m'
                    print(pstr)
                    return False
            else:
                pstr = "服务器host:\033[1;35m" + str(result["msg"]["host"]) + ":" + str(
                    result["msg"]["port"]) + "\033[0m,测试命令执行失败)\n"
                pstr += str(result["msg"]["info"])
                print(pstr)
                return False
        print("----------------------------------------------------------\n")
        return True

    def del_tmp_nginx_file(self):
        cmd = "rm /usr/local/nginx/conf/conf.d/tmp*.conf"
        self.__cmd(cmd)

    def check_server(self):
        for host in self.server_list:
            srv = self.srv.get_server(host)
            if len(srv) == 0:
                print("没有\033[1;32m hostname \033[0m为\033[1;32m " + host + " \033[0m的服务器")
                exit(2)
            srv_info = self.srv.get_decode_srv_info(srv)
            can_conn = self.check_connect(srv_info)
            if not can_conn:
                print("连接服务器:\033[1;35m" + srv_info["host"] + "\033[0m失败!")
                exit(1)

    def check_connect(self, server_info):
        try:
            sh = paramiko.SSHClient()
            sh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            sh.connect(hostname=server_info["host"], port=server_info["port"], username=server_info["user"],
                       password=server_info["password"])
            stdin, stdout, stderr = sh.exec_command("hostname")
            print("连接服务器:\033[1;32m" + stdout.read().decode() + "\033[0m成功!")
            sh.close()
            self.normal_server_list.append(server_info)
        except Exception as err:
            return False
        return True

    def push_code_all(self):
        ok, msg = self.push_code()
        if not ok:
            return False, msg

        ok, msg = self.rsync_data()
        if not ok:
            return False, msg

        ok, msg = self.create_ln()
        if not ok:
            return False, msg

        return True, self.codepath

    def push_code(self):
        if self.csrv.cigroupfolder == "":
            self.csrv.cigroupfolder = self.csrv.group_name + "_" + time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        cmd = "/files/sh/upload/upload_" + self.csrv.type + ".sh " + self.csrv.cigroupfolder + " default publish " + self.csrv.admin_branch + self.csrv.api_branch + self.csrv.common_branch
        output = self.__local_cmd(cmd)
        output_arr = output.split("\n")

        for line in output_arr:
            if "backupfile" in line:
                self.csrv.backup_file = line.split("backupfile:")[1]
                self.csrv.publish_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                break
        if self.csrv.backup_file == "":
            return False, "获取backupfile 失败"
        return True, ""

    def rollback_code_all(self, backup_file):
        ok, msg = self.rollback_code(backup_file)
        if not ok:
            return False, msg

        ok, msg = self.rsync_data()
        if not ok:
            return False, msg

        ok, msg = self.create_ln()
        if not ok:
            return False, msg

        return True, self.codepath

    def rollback_code(self, backup_file):
        cmd = "/files/sh/upload/upload_" + self.csrv.type + ".sh " + self.csrv.cigroupfolder + " default rollback " + backup_file
        output = self.__local_cmd(cmd)
        output_arr = output.split("\n")

        for line in output_arr:
            if "backupfile" in line:
                self.csrv.backup_file = line.split("backupfile:")[1]
                self.csrv.publish_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                break
        if self.csrv.backup_file == "":
            return False, "获取backupfile 失败"
        return True, ""

    def rsync_data(self):
        if self.csrv.cigroupfolder == "":
            print("cigroupfolder不存在")
            exit(2)
        if len(self.normal_server_list) == 0:
            print("没有可用的服务器连接")
            exit(2)

        fullpath = "/files/php/" + self.type + "/" + self.csrv.cigroupfolder + "/default"
        self.codepath = "/files/php/" + self.type + "/code/" + self.csrv.group_name + "_default_" + self.get_code_timestamp()
        cmd = "mkdir -p " + self.codepath + " && rsync -avrztpogPW --delete -e 'ssh -p 22' root@192.168.0.31:" + fullpath + "/. " + self.codepath + " > /dev/null"
        # print(cmd)
        result_list = self.__cmd(cmd)
        for result in result_list:
            if not result["status"]:
                return False, result["host"] + ":" + result["port"] + ":" + result["msg"]["info"]
        return True, {}

    def create_ln(self):
        if self.codepath == "":
            print("codepath不存在")
            exit(2)

        cmd = "ln -s /files/php/" + self.type + "/data " + self.codepath
        cmd += " && ln -s /files/php/" + self.type + "/upload " + self.codepath
        # print(cmd)
        result_list = self.__cmd(cmd)
        for result in result_list:
            if not result["status"]:
                return False, result["host"] + ":" + result["port"] + ":" + result["msg"]["info"]
        return True, {}

    def create_ln_to_code(self):
        if self.type == "" or self.csrv.group_name == "":
            return False, "type或者cigroup_name为空"

        self.csrv.pto = self.csrv.group_name + "_default_" + self.code_timestamp
        self.csrv.pto_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        group_codepath = "/files/php/" + self.type + "/" + self.csrv.group_name + "/default"
        cmd = "mkdir -p " + group_codepath
        cmd += " && rm -r " + group_codepath
        cmd += " && ln -s " + self.codepath + " " + group_codepath
        # print(cmd)
        result_list = self.__cmd(cmd)
        for result in result_list:
            if not result["status"]:
                return False, result["msg"]["info"]
        return True, {}

    def reload_php(self):
        cmd = "service php7.2-fpm reload"
        result_list = self.__cmd(cmd)
        for result in result_list:
            if not result["status"]:
                return False, result["host"] + ":" + result["port"] + ":" + result["msg"]["info"]
        return True, {}

    def __sftp_push(self, file, to_file):
        print(3333)
        print(self.normal_server_list)
        self.sftp_status_list = []
        for srv in self.normal_server_list:
            try:
                t = paramiko.Transport(srv["host"], srv["port"])
                t.connect(username=srv["user"], password=srv["password"])
                sftp = paramiko.SFTPClient.from_transport(t)
                sftp.put(file, to_file)
                t.close()
                status = {"status": True, "msg": "", "server": srv}
                self.sftp_status_list.append(status)
            except Exception as err:
                status = {"status": False, "msg": str(err), "server": srv}
                self.sftp_status_list.append(status)

    def __cmd(self, comand):
        if len(self.normal_server_list) == 0:
            print("没有可用的服务器连接")
            exit(2)

        result_list = []
        for srv in self.normal_server_list:
            try:
                sh = paramiko.SSHClient()
                sh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                sh.connect(hostname=srv["host"], port=srv["port"], username=srv["user"], password=srv["password"])
                stdin, stdout, stderr = sh.exec_command(comand)
                stdout = stdout.read().decode()
                stderr = stderr.read().decode()
                sh.close()
                result = {
                    "status": True,
                    "msg": {
                        "host": srv["host"],
                        "port": srv["port"],
                        "info": stdout + "-----------------------\n" + stderr
                    }
                }
                result_list.append(result)

            except Exception as err:
                result = {
                    "status": False,
                    "msg": {
                        "info": str(err)
                    }
                }
                result_list.append(result)

        return result_list

    def __local_cmd(self, comand):
        p = os.popen(comand)
        output = p.read()
        return output

    # srv_info = {
    #     "user": "root",
    #     "password": "wycr-live-ninw@3"
    # }
    # encode_srv_info = self.srv.get_encode_srv_info(srv_info)
    # print(encode_srv_info)
