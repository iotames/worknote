import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import configparser
import os
import logging
logger = logging.getLogger(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("odoo_db_con")


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
            logger.info(f"成功连接到PostgreSQL数据库: {self.database}")
            
            # 测试连接
            self.cursor.execute("SELECT version();")
            version = self.cursor.fetchone()
            logger.info(f"PostgreSQL版本: {version['version']}")
            
        except Exception as e:
            raise Exception(f"连接PostgreSQL失败: {e}")
    
    def execute_query(self, query, params=None):
        """执行查询语句"""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            self.connection.rollback()
            return None
    
    def close(self):
        """关闭连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("数据库连接已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# 获取数据库连接
def get_db_connection(config):
    """根据配置获取数据库连接
    
    Args:
        config: Config对象，包含数据库连接配置
        
    Returns:
        PostgreSQLConnector: 数据库连接实例
    
    Raises:
        Exception: 当无法建立数据库连接时抛出异常
    """
    try:
        # 从配置中获取数据库参数
        host = config.host
        port = config.port
        database = config.database
        username = config.username
        password = config.password
        
        # 创建并返回数据库连接
        db = PostgreSQLConnector(host, port, database, username, password)
        return db
    except Exception as e:
        raise Exception(f"建立数据库连接失败: {str(e)}")