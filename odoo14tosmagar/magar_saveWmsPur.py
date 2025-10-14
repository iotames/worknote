import json
import time
import requests
import logging
from get_conf import Config
from odoo_db_con import get_db_connection
from funcs import extract_single_weight

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("magar_saveWmsPur")

# 常量定义
COMPANY_ID = 2
API_ENDPOINT = '/yzApi/saveWmsPur'
TIME_INTERVAL = '6 HOURS'
QUERY_LIMIT = 500


def main():
    config = None
    str_token = None
    db = None
    
    try:
        # 读取配置信息
        config = Config()
        baseURL = config.baseURL
        str_token = config.token
        TIME_INTERVAL = config.time_interval
        
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
        # 连接数据库并查询采购合同
        db = get_db_connection(config)
        logger.info("开始查询采购合同")
        
        # 构造查询语句
        query = f"""
                    SELECT  distinct a.name , 
                            case when a.type = 'B' then 1 else 2 end as matetype, 
                            a.create_date, 
                            a.delivery_date as delivery_date, 
                            a.tax_rate , 
                            a.currency_rate ,
                            a.id ,
                            b.code as supplier_code, 
                            b.name as supplier_name , 
                            d.contract_no , 
                            g.design_no as itemcode ,
                            h.name as currency , 
                            i.login as creater,
                            j.phone , 
                            j.represent ,
                            a.id as purchase_order_id , 
                            f.id as order_line_id 
                    FROM    public.ziyi_purchase_order a inner join 
                            public.ziyi_base_partner b on a.supplier_id = b.id inner join 
                            public.ziyi_purchase_order_line c on c.order_id = a.id inner join 
                            public.ziyi_sale_order_line f on f.id = c.sale_order_line inner join 
                            public.ziyi_sale_order d on d.id = f.order_id inner join 
                            public.ziyi_product g on g.id = f.product_id inner join 
                            public.res_currency h on h.id = a.currency_id left join 
                            public.res_users i on i.id = a.create_uid inner join 
                            public.ziyi_base_partner j on j.id = a.supplier_id 
                    WHERE   a.active = true and 
                            a.state = 'audit'
                            AND a.write_date > CURRENT_TIMESTAMP - INTERVAL '{TIME_INTERVAL}' 
                    LIMIT {QUERY_LIMIT};
                """
        
        results = db.execute_query(query)
        
        if not results:
            logger.info("没有符合条件的采购合同")
            return
        
        logger.info(f"共查询到 {len(results)} 条采购合同")
        
        for rec in results:
            wms_pur_list = []
            query_mate = """
                        select  material_material_id , 
                                material_color_id , 
                                material.code as matecode , 
                                material.name as matename ,
                                material.weight ,
                                material_name as model,
                                order_line.quantity as qty , 
                                order_line.price ,
                                order_line.total_price ,
                                unit.name as mateunit , 
                                color.name as colorname,
                                color.code as colorcode
                        from    public.ziyi_purchase_order_line order_line inner join 
                                public.ziyi_base_material material on material.id = order_line.material_material_id inner join 
                                public.ziyi_base_unit unit on unit.id = material.unit_id inner join 
                                public.ziyi_base_color color on color.id = order_line.material_color_id 
                        where   order_line.order_id = %s 
                                and order_line.active = true
                                and order_line.sale_order_line = %s
                        order by order_line.order_id , order_line.sequence 
                        """
            
            results_mate = db.execute_query(query_mate, [rec['purchase_order_id'], rec['order_line_id']])
            
            if not results_mate:
                logger.info(f"采购合同 {rec['name']} 没有符合条件的物料")
                continue
                
            for mate in results_mate:
                weight = extract_single_weight(mate['weight'])
                wms_pur_list.append({
                    "idx" : len(wms_pur_list) + 1, # 序号  自增
                    "mateCode": mate['matecode'],
                    "mateName": mate['matename'],
                    "mateUnit": mate['mateunit'],
                    "qty": str(mate['qty']),
                    "colorCode": mate['colorcode'],
                    "colorName": mate['colorname'],
                    "model": mate['model'],
                    "weight": weight,
                    # 单价和金额是根据币种单价和金额换算的
                    "currPrice": float(str(mate['price'])), # 币种单价
                    "currAmount": float(str(mate['total_price'])), # 币种金额
                })

            
            orderbillno = f"{rec['contract_no']}_{rec['itemcode']}"
            billno = f"{rec['name']}_{orderbillno}"
            data = {
                    'billNo':   billno,  # 采购单号
                    'mateType': rec['matetype'],
                    'fillDate': rec['create_date'].strftime("%Y-%m-%d"),
                    'providerCode': rec['supplier_code'],
                    'providerName': rec['supplier_name'],
                    'deliveryDate': rec['delivery_date'].strftime("%Y-%m-%d"),
                    'orderBillNO' : orderbillno,  # 生产订单号
                    'deliveryType': '' , # 交货方式'??
                    'taxRate': str(rec['tax_rate']) if rec['tax_rate'] else '0.0', # 税率
                    'currency': rec['currency'], # 币种
                    'exchangeRate': str(rec['currency_rate']), # 汇率
                    'creater':  rec['creater'], # 创建人(admin)
                    'checkTime' : rec['create_date'].strftime("%Y-%m-%d"), # 审核日期 (yyyy-MM-dd HH:mm:ss)????
                    'linkName': rec['represent'], # 联系人
                    'linkTel' : rec['phone'], # 联系电话
                    'state':1, # 状态 (状态：0:未审核；1:已审核；2，已作废；3，已结案)  默认为1
                    'wmsPurListList': wms_pur_list
                    }
            
            # 调用API写入数据
            url = baseURL + API_ENDPOINT
            headers = {
                "Content-Type": "application/json",
                "smagar-token": str_token
            }
            
            logger.info(f"开始调用API写入采购合同: {billno}")
            logger.debug(f"请求数据: {data}")
            
            try:
                response = requests.post(url, headers=headers, json=data, timeout=30)
                response.raise_for_status()  # 检查HTTP错误
                
                # 尝试解析JSON响应
                response_data = response.json()
                logger.info(f"API调用成功，响应: {response_data}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API请求失败: {e}")
            except json.JSONDecodeError:
                logger.error(f"JSON解析错误，响应内容: {response.text if 'response' in locals() else '无响应'}")
            except Exception as e:
                logger.error(f"API调用异常: {str(e)}")
                
    except Exception as e:
        logger.error(f"处理过程中发生错误: {e}")
    finally:
        # 确保资源正确释放
        if db:
            try:
                db.close()
                logger.info("数据库连接已关闭")
            except Exception as e:
                logger.error(f"关闭数据库连接时发生错误: {e}")


if __name__ == "__main__":
    main()