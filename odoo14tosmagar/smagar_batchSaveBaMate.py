import requests
import json
import time
import logging
from get_conf import Config
from odoo_db_con import get_db_connection

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("smagar_batchSaveBaMate")

# 常量定义
TIME_INTERVAL = '2 HOURS'
QUERY_LIMIT = 500
API_ENDPOINT = '/yzApi/batchSaveBaMate'

# todo : 读取配置文件中的smanager_token , 如果不存在或者已过期, 则获取新的token
def main():
    str_token = ""
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
        logger.info("开始查询物料资料")
        
        # 构造查询语句
        query = f"""
                    SELECT  a.id as material_id, a.code, a.name, a.create_date , 
                            case when b.code = 'B' then '1' else '2' end as matetype , 
                            case when a.active then '1' else '0' end as state , 
                            c.name as unit ,
                            a.composition ,
                            d.full_code as categorycode,
                            d.name as categoryname , 
                            e.code as supplier_code,
                            e.name as supplier_name
                    FROM    public.ziyi_base_material a inner join 
                            public.ziyi_base_material_type b on b.id = a.type_id inner join 
                            public.ziyi_base_unit c on c.id = a.unit_id inner join 
                            public.ziyi_base_mat_category_first d on d.id = a.first_id left join 
                            public.ziyi_base_partner e on e.id = a.supplier_id
                    WHERE   a.write_date > CURRENT_TIMESTAMP - INTERVAL '{TIME_INTERVAL}' 
                    LIMIT {QUERY_LIMIT}
        """
        
        results = db.execute_query(query)
        
        if not results:
            logger.info("没有物料资料")
            return
        
        list_value = []
        for res in results:
            # 查询物料明细表, 获取规格和颜色
            query_detail = """
                                select  distinct  e.name as model_name, f.name as color_name, f.code as color_code
                                from    ziyi_base_material_details e inner join 
                                        ziyi_base_color f on f.id = e.color_id  
                                where  e.material_id = %s
                            """
            results_detail = db.execute_query(query_detail, (res['material_id'],))
            modelList = []
            colorList = []
            orderId_model = 1
            orderId_color = 1
            for res_detail in results_detail:
                if res_detail['model_name'] not in [item['model'] for item in modelList]:
                    modelList.append({
                        "model": res_detail['model_name'],
                        "orderId": orderId_model
                    })
                    orderId_model += 1
                if res_detail['color_code'] not in [item['colorCode'] for item in colorList]:
                    colorList.append({
                        "colorCode": res_detail['color_code'],
                        "colorName": res_detail['color_name'],
                        "orderId": orderId_color
                    })
                    orderId_color += 1

            material_data = {
                'code': res['code'] or res['name'],
                'name': res['name'],
                'createTime': res['create_date'].strftime('%Y-%m-%d %H:%M:%S'),
                'mateType': res['matetype'],
                'state': res['state'],
                'categoryCode': res['categorycode'],
                'categoryName': res['categoryname'],
                'unit': res['unit'],
                'element': res['composition'],
                'providerCode': res['supplier_code'] ,
                'providerName': res['supplier_name'] ,
                "modelList": modelList,
                "colorList": colorList,
            }
            logger.debug(f"准备的物料数据: {material_data}")
            list_value.append(material_data)
            
        logger.info(f"共准备 {len(list_value)} 条物料数据")
        
        # 写入mes接口
        url = baseURL + API_ENDPOINT
        headers = {
            "Content-Type": "application/json",
            "smagar-token": str_token
        }
        
        logger.info("开始写入物料资料到MES系统")
        logger.info(f"发送物料数据: {list_value}")
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
                
            logger.info("物料资料写入完成")
            
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