#!/bin/bash
basePath='/files/php/wycr/'
backupFilePath='/files/php/wycr/backup_file'
#s1_2020-03-23_14-23-00
if [ "" = "${1}" ]
then
    echo "请输入要cigroupname"
    exit
fi
#default
if [ "" = "${2}" ]
then
    echo "请输入要文件夹"
    exit
fi
#publish
if [ "publish" != "${3}" ] && [ "rollback" != "${3}" ]
then
    echo "请输入要操作的内容--publish:上线,rollback:回滚"
    exit
fi
#/files/php/wycr/s1_2020-03-23_14-23-00
filePath=${basePath}${1}
#default
folderPath=${2}
#publish
action=${3}
#master
admin_branch=api_branch=common_branch="master"
if [ "" != "${4}" ]
then
    admin_branch="${4}"
fi
if [ "" != "${5}" ]
then
    api_branch="${5}"
fi
if [ "" != "${6}" ]
then
    common_branch="${6}"
fi
#s1
cigroupname=${1%%_*}
#上线代码
if [ "publish" = ${action} ]
then
    if [ ! -d ${filePath} ]
    then
	    mkdir -p ${filePath}
    fi
    if [ ! -d "${filePath}/${folderPath}" ]
    then
	    mkdir -p ${filePath}/${folderPath}
    else
	    rm -rf ${filePath}/${folderPath}
	    mkdir -p ${filePath}/${folderPath}
    fi
    for path in "admin" "api" "common"
    do
        if [ "admin" == path ]
        then
            branch=$admin_branch
        elif [ "api" == path ]
        then
            branch=$api_branch
        else
            branch=$common_branch
        fi
        gitPath="/files/php/wycr_${path}_git"
        
        if [[ "api" == $path ]] || [[ "admin" == $path ]]
        then
            destinationPath=${filePath}/${folderPath}/${path}/
        else
            destinationPath=${filePath}/${folderPath}/
        fi
        
        cd $gitPath
        
        git pull
        git checkout $branch
        if [ $? -eq 1 ]
        then
	        echo "你的程序没有分支${branch}请检查"
	        exit
        fi
        git pull
	    
        #复制代码过去,只复制相关文件夹
        for folder in `ls -a | awk  '$1!=".git" && $1!=".idea" && $1!="." && $1!=".."{print $1}'`
        do
            if [ ! -d $destinationPath ]
            then
                mkdir -p $destinationPath
            fi
	        cp -rp $folder $destinationPath
        done
    done
    
    #备份打包数据
    date=`date "+%y-%m-%d_%H-%M-%S"`
    cd ${filePath}/${folderPath}
    if [ ! -d "${backupFilePath}/${cigroupname}/${folderPath}" ]
    then
	    echo "${backupFilePath}/${cigroupname}/${folderPath}"
	    mkdir -p ${backupFilePath}/${cigroupname}/${folderPath}
    fi
    tar -czf "${backupFilePath}/${cigroupname}/${folderPath}/${date}.tar.gz"  ./*
    echo "backupfile:${cigroupname}/${folderPath}/${date}.tar.gz"
    exit 0
#回滚代码
else
    echo "rollback"
    if [ "" = "${4}" ]
    then
        echo "请输入备份文件路径:eg: live/default/18-12-18_19-22-08.tar.gz "
        exit
    fi
    backupFile=${backupFilePath}/${4}
    if [ ! -d "${backupFilePath}/tmp" ]
    then
        mkdir -p ${backupFilePath}/tmp
    fi
    cd ${backupFilePath}/tmp
    rm -rf ${backupFilePath}/tmp/*
    tar -xzf ${backupFile}
    if [ -d "${filePath}/${folderPath}" ]
    then
        rm -rf ${filePath}/${folderPath}
    fi
    mkdir -p ${filePath}/${folderPath}
    if [ $? -eq 1 ]
    then
        echo "没有这个备份文件....${backupFile}"
    exit 1
    fi 
    mv ${backupFilePath}/tmp/* ${filePath}/${folderPath}
    echo "backupfile:${4}"
    exit 0
fi
