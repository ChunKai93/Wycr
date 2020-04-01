# 午夜超人代码上线工具Python版本
---
## 目录
- bash:bash脚本
    - upload_wycr.sh
- conf:配置文件
    - cigroup_wycr.json:主配置,测试环境和生产环境
    - group.json:服务器分组信息
    - server.json:服务器信息,账号密码等
- foo:主要包
    - option:
        - option.py:命令行参数处理
    - server:
        - ciserver.py:主配置文件相关处理
        - server.py:服务器相关处理
        - shell.py:shell操作
- main.py:入口文件
- requirement.txt:项目依赖包列表

---
## cigroup_wycr.json
测试机(生产机)模板:
```
"s1": {
        "cigroupfolder": null,
        "folder": {
            "backup_file": null,
            "branch": {
                "admin": "master",
                "api": "master",
                "common": "master"
            },
            "last_backup_file": null,
            "pto": null,
            "pto_time": null,
            "publish_time": null
        },
        "nginx": {
            "listenlist": [
                {
                    "port": 80,
                    "ssl": false
                }
            ],
            "servername": {
                "admin": "a-s1.test.wycr888.com",
                "api": "api-s1.test.wycr888.com"
            }
        },
        "server_group": "test",
        "server_type": "g"
    }
```
- s1:测试机(生产机)标识
- branch:分支;admin对应仓库wycr_admin;api对应仓库wycr_api;common对应仓库wycr_common
- servername:域名;admin对应后台的域名;api对应api的域名;
- server_group:服务器分组信息;测试机填test,生产机填live;

---
### 使用---命令
展示某个测试机的nginx配置信息,如s1:
```
nupl -c shownginx -g s1
```
```
api配置: 
server {
    listen 80;
    server_name api-s1.test.wycr888.com;
    
    root /files/php/wycr/s1/default/api;
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
        access_log off;
        expires 30d;
    }
    
    location ~ .*\.(js|css)?$ {
        access_log off;
        expires 1h;
    }
    access_log  /usr/local/nginx/logs/wycr_api_s1.log main;
}

admin配置: 
server {
    listen 80;
    server_name a-s1.test.wycr888.com;

    root /files/php/wycr/s1/default/admin;
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
        access_log off;
        expires 30d;
    }

    location ~ .*\.(js|css)?$ {
        access_log off;
        expires 1h;
    }
    access_log  /usr/local/nginx/logs/wycr_admin_s1.log main;
}

```

生成nginx配置信息
```
nupl -c pushnginx -g s1
```

提交代码到测试机
```
nupl -c push -g s1
```

提交代码到生产机
```
nupl -c push -g live
```

回滚测试机代码,指定备份文件,备份文件存于/files/php/wycr/backup_file/,确保备份文件存在:
```
nupl -c rollback -g s1 -b s1/default/20-03-31_16-01-35.tar.gz
```

回滚生产机代码,指定备份文件,备份文件存于/files/php/wycr/backup_file/,确保备份文件存在:
```
nupl -c rollback -g live -b live/default/20-03-31_16-01-35.tar.gz
```
