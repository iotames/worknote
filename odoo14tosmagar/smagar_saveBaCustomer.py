import time
import json
import logging
import requests
from get_conf import Config
from odoo_db_con import get_db_connection

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("smagar_saveBaCustomer")

# 常量定义
TIME_INTERVAL = '2 HOURS'
QUERY_LIMIT = 500
API_ENDPOINT = '/yzApi/saveBaCustomer'

# todo : 读取配置文件中的smanager_token , 如果不存在或者已过期, 则获取新的token
def main():
    """主函数，从Odoo数据库查询客户资料并写入MES系统"""
    config = None
    str_token = None
    db = None  # 初始化db变量
    try:
        # 读取配置信息
        config = Config()
        baseURL = config.baseURL
        str_token = config.token
        TIME_INTERVAL = config.timeinterval
        
        logger.info("配置信息加载成功")
        logger.debug(f"baseURL: {baseURL}")
        
    except FileNotFoundError as e:
        logger.error(f"配置文件错误: {e}")
        return
    except Exception as e:
        logger.error(f"读取配置信息时发生错误: {e}")
        return
    
    if not str_token:
        logger.error("无法获取有效的token，无法继续操作")
        return
        
    try:
        # 连接数据库并查询客户资料
        db = get_db_connection(config)  
        logger.info("开始查询客户资料")
        
        # 构造查询语句
        query = f"""
            SELECT  code, name, short_name, memo, phone, address 
            FROM    public.ziyi_base_partner 
            WHERE   (customer = true OR brand = true)
                    AND write_date > CURRENT_TIMESTAMP - INTERVAL '{TIME_INTERVAL}' 
            LIMIT   {QUERY_LIMIT}
        """
        
        results = db.execute_query(query)
        
        if not results:
            logger.info("没有符合条件的客户资料")
            return
            
        # 处理查询结果
        list_value = []
        for res in results:
            # 注意：这里重命名变量以避免覆盖导入的json模块
            customer_data = {
                'code': res['code'],
                'name': res['name'],
                'shortName': res['short_name'],
                # 'headquarters': '',
                'remark': res['memo'],
                # 'linkName': '',
                'linkTel': res['phone'],
                'linkAdress': res['address']
            }
            
            # 只在debug级别记录详细数据
            logger.debug(f"处理客户数据: {customer_data}")
            list_value.append(customer_data)
            
        logger.info(f"共处理 {len(list_value)} 条客户数据")
        
        # 调用API写入客户资料
        url = baseURL + API_ENDPOINT  # 使用已有的config实例，避免重复创建
        headers = {
            "Content-Type": "application/json",
            "smagar-token": str_token
        }
        
        logger.info(f"开始写入客户资料到MES系统，API地址: {url}")
        logger.info(f"发送客户数据: {list_value}")
        try:
            response = requests.post(url, headers=headers, json=list_value, timeout=60)
            
            # 检查HTTP响应状态
            if response.status_code != 200:
                logger.error(f"API请求失败，状态码: {response.status_code}, 响应内容: {response.text}")
                # 可以选择抛出异常或直接返回
                # raise requests.exceptions.HTTPError(f"API请求失败: {response.status_code}")
                return
            
            # 尝试解析JSON响应
            try:
                response_data = response.json()
                logger.info(f"API响应: {response_data}")
            except json.JSONDecodeError:
                logger.error(f"API返回非JSON格式响应: {response.text}")
                
            logger.info("客户资料写入完成")
            
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