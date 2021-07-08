from pymysql.cursors import DictCursor
from dbutils.pooled_db import PooledDB
from . import mysql_config as config


class MysqlPool:
    """pool store for mysql"""

    __pool = None

    def __init__(self):
        # 触发创建连接池
        self.conn = self.__getConn()
        self.cursor = self.conn.cursor()

    # 创建数据库连接池
    def __getConn(self):
        if self.__pool is None:
            self.__pool = PooledDB(
                creator=config.DB_CREATOR,
                mincached=config.DB_MIN_CACHED,
                maxcached=config.DB_MAX_CACHED,
                maxshared=config.DB_MAX_SHARED,
                maxconnections=config.DB_MAX_CONNECTIONS,
                blocking=config.DB_BLOCKING,
                maxusage=config.DB_MAX_USAGE,
                setsession=config.DB_SET_SESSION,
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                passwd=config.DB_PASSWD,
                db=config.DB_NAME,
                use_unicode=False,
                charset=config.DB_CHARSET,
                cursorclass=DictCursor
            )

        return self.__pool.connection()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.conn.close()

    # 从连接池中获取一个连接
    def getConn(self):
        conn = self.__getConn()
        cursor = conn.cursor()
        return cursor, conn


def get_mysql_connection():
    return MysqlPool()
