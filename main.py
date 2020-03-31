#!/usr/bin/python3
import sys
import io
import os
from foo.option import option
from foo.server import ciserver, server, shell


def setup_io():
    sys.stdout = sys.__stdout__ = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', line_buffering=True)
    sys.stderr = sys.__stderr__ = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', line_buffering=True)


def main(opt_dict):
    csrv = ciserver.Ciserver(opt_dict["type"])
    srv = server.Server()
    sh = shell.Shell(opt_dict["type"])

    if opt_dict["comand"] == "showcigroup":
        group_list = csrv.get_group_list()
        print(group_list)
    elif opt_dict["comand"] == "showgroup":
        group_list = srv.get_group_list()
        print(group_list)
    elif opt_dict["comand"] == "shownginx":
        err, nginx = csrv.get_nginx(opt_dict["cigroupname"])
        if err is not True:
            print("没有这个\033[1;35mcigroup\033[0m,请先自行编辑\033[1;35mconf/cigroup_" + opt_dict["type"] + ".txt\033[0m")

        print("\033[1;32mapi配置:\033[0m \n" + nginx["api"] + "\n")
        print("\033[1;32madmin配置:\033[0m \n" + nginx["admin"])
    elif opt_dict["comand"] == "pushnginx":
        print("会生成或覆盖 \033[1;35mapi-" + opt_dict["cigroupname"] + "." + opt_dict["type"] + ".com.conf\033[0m")
        print("会生成或覆盖 \033[1;35ma-" + opt_dict["cigroupname"] + "." + opt_dict["type"] + ".com.conf\033[0m")
        err, nginx = csrv.get_nginx(opt_dict["cigroupname"])
        if err is not True:
            print("没有这个\033[1;35mcigroup\033[0m,请先自行编辑\033[1;35mconf/cigroup_" + opt_dict["type"] + ".txt\033[0m")
            exit(1)
        print("\033[1;32mapi配置:\033[0m \n" + nginx["api"] + "\n")
        print("\033[1;32madmin配置:\033[0m \n" + nginx["admin"])

        ok = input("\033[1;32m请最后确认一下nginx配置,确认修改(y),直接退出(n):y?n\033[0m")
        if ok == "y":
            csrv_type, csrv_info, msg = csrv.get_server_info(opt_dict["cigroupname"])
            if csrv_type in ["g", "s"]:
                if csrv_type == "g":
                    group = srv.get_group(csrv_info)
                    if len(group) == 0:
                        print("\033[1;31m没有这个分组\033[0m")
                    sh.set_group(csrv_info, group)
                    sh.set_nginx(nginx)
                    sh.check_server()
                    sh.push_nginx()
                else:
                    print("\033[1;31m待完善\033[0m")
                    exit(2)

                ok = sh.check_nginx()
                if not ok:
                    sh.del_tmp_nginx_file()
                else:
                    ok, msg = sh.push_code_all()
                    if not ok:
                        sh.del_tmp_nginx_file()
                        print("\033[1;33m" + msg + "\033[0m")
                        exit(2)
                    else:
                        ok = input("\033[1;32m代码已经就绪,是否指向新代码:y?n\033[0m")
                        if ok == "y":
                            ok, msg = sh.create_ln_to_code()
                            if not ok:
                                print("\033[1;33m" + msg + "\033[0m")
                                exit(2)

                            ok, msg = sh.save_nginx()
                            if not ok:
                                print("\033[1;33m" + msg + "\033[0m")
                                exit(2)

                            csrv.save_cigroup(opt_dict["cigroupname"])
                            print("\033[1;32m上线完成,请检查\033[0m")
                        else:
                            print("准备好的代码路径为:\033[1;32m" + msg + "\033[0m")
                            print("\033[1;32mBye\033[0m")
            else:
                print("\033[1;31m" + msg + "\033[0m")
        else:
            print("\033[1;32m您没有确定\033[0m")
            print("\033[1;32mBye\033[0m")
    elif opt_dict["comand"] == "push":
        csrv_type, csrv_info, msg = csrv.get_server_info(opt_dict["cigroupname"])
        if csrv_type in ["g", "s"]:
            if csrv_type == "g":
                group = srv.get_group(csrv_info)
                if len(group) == 0:
                    print("\033[1;31m没有这个分组\033[0m")
                sh.set_group(csrv_info, group)
            else:
                print("\033[1;31m待完善\033[0m")
                exit(2)

            sh.check_server()
            ok, msg = sh.push_code_all()
            if not ok:
                print("\033[1;33m" + msg + "\033[0m")
                exit(2)
            else:
                ok, msg = sh.create_ln_to_code()
                if not ok:
                    print("\033[1;33m" + msg + "\033[0m")
                    exit(2)

                ok, msg = sh.reload_php()
                if not ok:
                    print("\033[1;33m" + msg + "\033[0m")
                    exit(2)

                csrv.save_cigroup(opt_dict["cigroupname"])
                print("\033[1;32m上线完成,请检查\033[0m")
        else:
            print("\033[1;31m" + msg + "\033[0m")
    elif opt_dict["comand"] == "rollback":
        csrv_type, csrv_info, msg = csrv.get_server_info(opt_dict["cigroupname"])
        if csrv_type in ["g", "s"]:
            if csrv_type == "g":
                group = srv.get_group(csrv_info)
                if len(group) == 0:
                    print("\033[1;31m没有这个分组\033[0m")
                sh.set_group(csrv_info, group)
            else:
                print("\033[1;31m待完善\033[0m")
                exit(2)

            print(opt_dict["backupfile"])
            sh.check_server()
            ok, msg = sh.rollback_code_all(opt_dict["backupfile"])
            if not ok:
                print("\033[1;33m" + msg + "\033[0m")
                exit(2)
            else:
                ok, msg = sh.create_ln_to_code()
                if not ok:
                    print("\033[1;33m" + msg + "\033[0m")
                    exit(2)

                ok, msg = sh.reload_php()
                if not ok:
                    print("\033[1;33m" + msg + "\033[0m")
                    exit(2)

                csrv.save_cigroup(opt_dict["cigroupname"])
                print("\033[1;32m回滚完成,请检查\033[0m")
        else:
            print("\033[1;31m" + msg + "\033[0m")
    elif opt_dict["comand"] == "addserver":
        print("addserver")


if __name__ == '__main__':
    setup_io()
    argv = sys.argv[1:]

    op = option.option()
    opt_dict = op.check_argv(argv)

    if opt_dict["help"] is True:
        op.useage()
    elif opt_dict["legal"] is False:
        print(opt_dict["err_info"])
        op.useage()
    else:
        main(opt_dict)
