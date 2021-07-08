from .mysql_pool import get_mysql_connection


class MysqlPoolWrap(object):

    def __init__(self):
        self.db = get_mysql_connection()

    # 单例
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'inst'):
            cls.inst = super(MysqlPoolWrap, cls).__new__(cls, *args, **kwargs)
        return cls.inst

    # 释放连接
    def close(self, cursor, conn):
        cursor.close()
        conn.close()

    def execute(self, sql, param=None, autoClose=False):
        cursor, conn = self.db.getConn()
        count = 0
        try:
            if param:
                count = cursor.execute(sql, param)
            else:
                count = cursor.execute(sql)
            conn.commit()
        except Exception as e:
            print(e)
            conn.rollback()

        if autoClose:
            self.close(cursor, conn)
        return cursor, conn, count

    def insertOne(self, sql, param=None):
        count = 0
        try:
            cursor, conn, count = self.execute(sql, param)
            conn.commit()
            self.close(cursor, conn)
            return count
        except Exception as e:
            print(e)
            conn.rollback()
            self.close(cursor, conn)
            return count

    def insertMany(self):
        pass

    def select(self, sql, param=None, mul=False):
        try:
            cursor, conn, count = self.execute(sql, param)
            if not mul:
                res = cursor.fetchone()
            else:
                res = cursor.fetchall()
            self.close(cursor, conn)
            return res
        except Exception as e:
            print(e)
            self.close(cursor, conn)
            return None

    def update(self, sql, param=None):
        count = 0
        try:
            cursor, conn, count = self.execute(sql, param)
            conn.commit()
            self.close(cursor, conn)
            return count
        except Exception as e:
            print(e)
            conn.rollback()
            self.close(cursor, conn)
            return count

    def getConn(self):
        return self.db.getConn()


