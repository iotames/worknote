import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import configparser
import os


class PostgreSQLConnector:
    def __init__(self, host , port , database , username , password):
        self.connection = None
        self.cursor = None
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self._connect()
    
    # def _load_config(self):
    #     """加载配置文件"""
    #     # if not os.path.exists(self.config_file):
    #     #     self._create_sample_config()
    #     #     raise FileNotFoundError(f"配置文件 {self.config_file} 不存在，已创建示例配置文件")
        
    #     config = configparser.ConfigParser()
    #     config.read(self.config_file, encoding='utf-8')
        
    #     self.host = config.get('POSTGRESQL', 'host', fallback='localhost')
    #     self.port = config.getint('POSTGRESQL', 'port', fallback=5432)
    #     self.database = config.get('POSTGRESQL', 'dbname', fallback='postgres')
    #     self.username = config.get('POSTGRESQL', 'dbuser', fallback='postgres')
    #     self.password = config.get('POSTGRESQL', 'dbpassword', fallback='password')
    
    def _connect(self):
        """连接PostgreSQL数据库"""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
                cursor_factory=RealDictCursor  # 返回字典格式的结果
            )
            self.cursor = self.connection.cursor()
            print(f"成功连接到PostgreSQL数据库: {self.database}")
            
            # 测试连接
            self.cursor.execute("SELECT version();")
            version = self.cursor.fetchone()
            print(f"PostgreSQL版本: {version['version']}")
            
        except Exception as e:
            raise Exception(f"连接PostgreSQL失败: {e}")
    
    def execute_query(self, query, params=None):
        """执行查询语句"""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"查询执行失败: {e}")
            self.connection.rollback()
            return None
    
    def close(self):
        """关闭连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("数据库连接已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# def main():
#     """主函数示例"""
#     try:
#         # 连接PostgreSQL
#         db = PostgreSQLConnector()

#         return db
           
#         # print("\n查询 - 用户信息:")
#         # query = """
#         # SELECT u.id
#         # FROM res_users u
#         # LIMIT 5;
#         # """
#         # users = db.execute_query(query)
#         # for user in users:
#         #     print(f"用户: {user['id']}")

#     except Exception as e:
#         print(f"错误: {e}")
#     finally:
#         if 'db' in locals():
#             db.close()

# if __name__ == "__main__":
#     main()