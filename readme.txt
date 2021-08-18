#安装kafka包,安装的是kafka-python，不是kafka。kafka是老得包
,#安装mysql包
执行pip3 install -r requirements.txt



pip3 install pymysql
pip3 install dbutils
pip3 install protobuf
pip3 install kafka-python
pip3 install redis


生成chia矿池protobuf协议
protoc --python_out=./proto/ chia.proto



安装python3依赖包
yum -y install zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel libffi-devel

Python 3.8.10
wget https://www.python.org/ftp/python/3.8.10/Python-3.8.10.tgz
cd Python-3.8.10
./configure --prefix=/usr/local/python3
make && make install
ln -s /usr/local/python3/bin/python3.8 /usr/bin/python3
ln -s /usr/local/python3/bin/pip3.8 /usr/bin/pip3

pool sql
/*
Navicat MySQL Data Transfer
Source Server         : chia矿池本地数据库
Source Server Version : 50734
Source Host           : 192.168.135.153:3306
Source Database       : chia_pool
Target Server Type    : MYSQL
Target Server Version : 50734
File Encoding         : 65001
Date: 2021-08-12 14:22:17
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for farmer
-- ----------------------------
DROP TABLE IF EXISTS `farmer`;
CREATE TABLE `farmer` (
  `launcher_id` varchar(500) NOT NULL,
  `p2_singleton_puzzle_hash` text,
  `delay_time` bigint(20) DEFAULT NULL,
  `delay_puzzle_hash` text,
  `authentication_public_key` text,
  `singleton_tip` blob,
  `singleton_tip_state` blob,
  `points` bigint(20) DEFAULT NULL,
  `difficulty` bigint(20) DEFAULT NULL,
  `payout_instructions` text,
  `is_pool_member` tinyint(4) DEFAULT NULL,
  PRIMARY KEY (`launcher_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for partial
-- ----------------------------
DROP TABLE IF EXISTS `partial`;
CREATE TABLE `partial` (
  `launcher_id` text,
  `timestamp` bigint(20) DEFAULT NULL,
  `difficulty` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

