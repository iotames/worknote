import json
import requests  # 添加这一行
from get_conf import Config
from odoo_db_con import get_db_connection
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("smagar_saveBaProvider")

# 常量定义
TIME_INTERVAL = '2 HOURS'
QUERY_LIMIT = 500
API_ENDPOINT = '/yzApi/saveBaProvider'

# todo : 读取配置文件中的smanager_token , 如果不存在或者已过期, 则获取新的token
def main():
    str_token = ""
    db = None  # 初始化db变量
    try:
        # 读取配置
        config = Config()
        baseURL = config.baseURL
        str_token = config.token
        TIME_INTERVAL = config.timeinterval
        
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
        db = get_db_connection(config)  
        logger.info("开始查询供应商资料")
        
        # 构造查询语句
        query = f"""
            SELECT  code, name, short_name, memo, phone, address, 
                    CASE WHEN supplier_material = true THEN '3' ELSE '4' END as providertype, 
                    represent
            FROM    public.ziyi_base_partner 
            WHERE   (
                        supplier_material = true 
                        OR supplier_processing = true 
                        OR supplier_service = true
                    )
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
        logger.info(f"发送供应商数据: {list_value}")
        try:
            response = requests.post(url, headers=headers, json=list_value, timeout=60)
            
            # 检查HTTP响应状态
            if response.status_code != 200:
                logger.error(f"API请求失败，状态码: {response.status_code}, 响应内容: {response.text}")
                return
            
            # 尝试解析JSON响应
            try:
                response_data = response.json()
                logger.info(f"API响应: {response_data}")
            except json.JSONDecodeError:
                logger.error(f"API返回非JSON格式响应: {response.text}")
                
            logger.info("供应商资料写入完成")
            
        except requests.exceptions.Timeout:
            logger.error(f"API请求超时，URL: {url}")
        except requests.exceptions.ConnectionError:
            logger.error(f"API连接错误，URL: {url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {e}")
        except Exception as e:
            logger.error(f"处理过程中发生错误: {e}")
    finally:
        # 确保数据库连接关闭
        if db:
            try:
                db.close()
            except Exception as e:
                logger.error(f"关闭数据库连接时发生错误: {e}")

if __name__ == "__main__":
    main()