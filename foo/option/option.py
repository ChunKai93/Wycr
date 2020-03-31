#!/usr/bin/python3
import getopt


class option(object):
    _instance = None

    # 单例模式(这种写法多线程会有问题)
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.comand_need_cigroupname = ["shownginx", "pushnginx", "push", "pointto", "pointlist", "rollback"]
        self.comand_not_need_cigroupname = ["showcigroup", "showgroup", "clearcachefile", "clearfield"]
        self.errinfo = ""

    def check_argv(self, a):
        try:
            shortopts = "hc:d:t:g:f:j:b:"
            longopts = ["help", "comand=", "dir=", "type=", "cigroupname=", "folder=", "json=", "backfile="]
            opts, _ = getopt.getopt(a, shortopts, longopts)
        except getopt.GetoptError as e:
            print(str(e) + ":参数值不能为空")
            exit(2)

        opt_dict = {"help": False, "legal": True, "type": "wycr", "cigroupname": None, "backupfile": None}
        for o, v in opts:
            if o in ("-h", "--help"):
                opt_dict["help"] = True
            elif o in ("-c", "--comand"):
                opt_dict["comand"] = v
            elif o in ("-d", "--dir"):
                opt_dict["ptodir"] = v
            elif o in ("-t", "--type"):
                opt_dict["type"] = v
            elif o in ("-g", "--cigroupname"):
                opt_dict["cigroupname"] = v
            elif o in ("-f", "--folder"):
                opt_dict["folder"] = v
            elif o in ("-j", "--json"):
                opt_dict["jsonfile"] = v
            elif o in ("-b", "--backupfile"):
                opt_dict["backupfile"] = v
            else:
                opt_dict["legal"] = False

        if opt_dict["type"] not in ["wycr"]:
            opt_dict["legal"] = False
            self.errinfo += "-t(type) 参数值错误\n"

        if "comand" in opt_dict.keys():
            if opt_dict["comand"] not in self.comand_need_cigroupname + self.comand_not_need_cigroupname:
                opt_dict["legal"] = False
                self.errinfo += "-c(command) 参数值错误\n"

            if opt_dict["comand"] in self.comand_need_cigroupname and opt_dict["cigroupname"] is None:
                opt_dict["legal"] = False
                self.errinfo += "-g(cigroupname) 参数不能为空\n"

            if opt_dict["comand"] == "rollback" and opt_dict["backupfile"] is None:
                opt_dict["legal"] = False
                self.errinfo += "-b(backupfile) 参数不能为空\n"

        opt_dict["err_info"] = self.errinfo
        return opt_dict

    def useage(self):
        s = """命令行帮助文档
            -h  --help          显示帮助文档
            -c  --comand        命令有：
                showcigroup(展示所有cigroup 配置)
                showgroup(展示所有group 配置)
                shownginx(展示要生成的nginx 配置)
                pushnginx(生成nginx配置文件)
                push(发布代码，后面参数为:-g cigroupname,-f foldername),pointto(指向文件夹,后面参数为:-d 指向的文件加 -f foldername) 
                rollback(回滚,后面参数为：-g cigroupname -j backup_****.json 或者 -g cigroupname -f foldername -b /files/php/wycr/backup_file/**/**/*****.tar.gz)
            -t  --type          业务主体,默认(wycr)
            -d  --dir           pointto的时候有用, 指向的文件夹 可参考-c的说明
            -g  --cigroupname   组名称,就是你在配置文件配置的组名称,比如:live,qa,s1,s2 ....
            -f  --folder        就是要处理的文件名称 可参考-c的说明 默认为(all)
            -b  --backfile      就是要回滚的备份文件, 可参考-c的说明
            """
        print(s)
