#!/usr/bin/python3
import os
import json
import base64
from Crypto import Random
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

random_generator = Random.new().read


class Server(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        p = os.popen("cat ~/.ssh/id_rsa")
        self.private_key = RSA.importKey(p.read())
        p.close()

        p = os.popen("ssh-keygen -e -m PEM -f ~/.ssh/id_rsa.pub")
        self.public_key = RSA.importKey(p.read())
        p.close()

        self.type = type
        self.group_list = None
        self.server_list = None

    def decode(self, decode_str):
        cipher = PKCS1_v1_5.new(self.private_key)
        return cipher.decrypt(base64.b64decode(decode_str), random_generator)

    def encode(self, str):
        cipher = PKCS1_v1_5.new(self.public_key)
        return base64.encodebytes(cipher.encrypt(str))

    def get_group_list(self):
        group_list = None
        try:
            group_file = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + "/conf/group.json"
            f = open(group_file, "r")
            group_list = f.read()
            f.close()

            self.group_list = json.loads(group_list)
        except Exception as err:
            print(str(err.__traceback__.tb_lineno))
            print(err)

        return group_list

    def get_group(self, groupname):
        if self.group_list is None:
            self.get_group_list()

        for k in self.group_list.keys():
            if k == groupname:
                return self.group_list[k]

        return []

    def get_server_list(self):
        server_list = None
        try:
            server_file = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + "/conf/server.json"
            f = open(server_file, "r")
            server_list = f.read()
            f.close()

            self.server_list = json.loads(server_list)
        except Exception as err:
            print(str(err.__traceback__.tb_lineno))
            print(err)

        return server_list

    def get_server(self, hostname):
        if self.server_list is None:
            self.get_server_list()

        for k in self.server_list.keys():
            if k == hostname:
                return self.server_list[k]

        return []

    def get_decode_srv_info(self, server_info):
        login_info = self.decode(server_info["info"]).decode().split(" ")
        server_info["user"] = login_info[0]
        server_info["password"] = login_info[1]
        del server_info["info"]
        return server_info

    def get_encode_srv_info(self, server_info):
        user_with_pw = server_info["user"] + " " + server_info["password"]
        encode_str = user_with_pw.encode()
        info = self.encode(encode_str)
        server_info["info"] = info
        del server_info["user"]
        del server_info["password"]
        return server_info

    def print_group(self):
        print(self.group_list)
