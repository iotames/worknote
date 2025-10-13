import requests
import json
from get_conf import Config
from odoo_db_con import PostgreSQLConnector
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 常量定义
COMPANY_ID = 2
TIME_INTERVAL = '2 HOURS'
QUERY_LIMIT = 500
API_ENDPOINT = '/yzApi/saveBaProvider'

# todo : 读取配置文件中的smanager_token , 如果不存在或者已过期, 则获取新的token
def main():
    str_token = ""
    try:
        # 读取配置
        config = Config()
        baseURL = config.baseURL
        str_token = config.token
        
        # 数据库配置
        host = config.host
        port = config.port
        database = config.database
        username = config.username
        password = config.password
        
    except FileNotFoundError as e:
        logger.error(f"配置文件错误: {e}")
        return
    except Exception as e:
        logger.error(f"读取配置时发生错误: {e}")
        return
        
    if not str_token:
        logger.error("错误: token 为空")
        return
        
    # 获取数据库连接
    try:
        db = PostgreSQLConnector(host, port, database, username, password)
        logger.info("开始查询供应商资料")
        
        # 构造查询语句
        query = f"""
            SELECT code, name, short_name, memo, phone, address, 
                   CASE WHEN supplier_material = true THEN '3' ELSE '4' END as providertype, 
                   represent
            FROM public.ziyi_base_partner 
            WHERE company_id = {COMPANY_ID} 
              AND (supplier_material = true OR supplier_processing = true OR supplier_service = true)
              AND write_date > CURRENT_TIMESTAMP - INTERVAL '{TIME_INTERVAL}' 
            LIMIT {QUERY_LIMIT}
        """
        
        results = db.execute_query(query)
        
        if not results:
            logger.info("没有符合条件的供应商资料")
            return
            
        # 准备数据
        list_value = []
        for res in results:
            provider_data = {
                'providerType': res['providertype'],
                'code': res['code'],
                'name': res['name'],
                'shortName': res['short_name'],
                'linkAdress': res['address'],
                'linkTel': res['phone'],
                'linkName': res['represent'],
                'remark': res['memo']
            }
            list_value.append(provider_data)
            
        logger.info(f"共准备 {len(list_value)} 条供应商数据")
        
        # 调用API保存数据
        url = baseURL + API_ENDPOINT
        headers = {
            "Content-Type": "application/json",
            "smagar-token": str_token
        }
        
        logger.info("开始写入供应商资料到MES系统")
        response = requests.post(url, headers=headers, json=list_value, timeout=30)
        response.raise_for_status()  # 检查HTTP错误
        
        logger.info(f"API响应: {response.json()}")
        logger.info("供应商资料写入完成")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API请求失败: {e}")
    except Exception as e:
        logger.error(f"处理过程中发生错误: {e}")

if __name__ == "__main__":
    main()