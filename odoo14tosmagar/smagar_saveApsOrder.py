import logging
import requests
from get_conf import Config
from odoo_db_con import get_db_connection
from funcs import get_product_bom, extract_single_weight

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("smagar_saveApsOrder")

# 常量定义
TIME_INTERVAL = '6 HOURS'
QUERY_LIMIT = 50
API_ENDPOINT = '/yzApi/saveApsOrder'
API_ENDPOINT_BOMS = '/yzApi/saveApsOrderBoms'
API_TIMEOUT = 60


def main():
    str_token = ""
    db = None
    try:
        # mes 配置
        config = Config()
        baseURL = config.baseURL
        str_token = config.token
        TIME_INTERVAL = config.timeinterval
        
    except FileNotFoundError as e:
        logger.error(f"配置文件错误: {e}")
        return
    except Exception as e:
        logger.error(f"配置加载错误: {e}")
        return

    try:
        # 获取数据库连接
        db = get_db_connection(config)  
        logger.info("开始查询订单")
        
        # 查询订单数据
        orders_data, boms_data = process_orders(db, TIME_INTERVAL)
        
        if not orders_data:
            logger.info("没有订单资料需要处理")
            return
        
        # 发送数据到API
        send_orders_to_api(baseURL, str_token, orders_data, boms_data)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API请求失败: {e}")
    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}")
    finally:
        # 确保数据库连接关闭
        if db and hasattr(db, 'close'):
            try:
                db.close()
                logger.info("数据库连接已关闭")
            except Exception as e:
                logger.error(f"关闭数据库连接时发生错误: {e}")


def process_orders(db, time_interval):
    """处理订单数据，返回订单和BOM数据"""
    query = f"""
                select  a.contract_no , b.code as cuscode , b.name as cusname , a.create_date , 
                        d.design_no as itemcode , d.id as product_id , c.id as order_line_id , 
                        f.login as creater , 
                        g.plan_date
                from    public.ziyi_sale_order a inner join 
                        public.ziyi_base_partner b on b.id = a.partner_id inner join 
                        public.ziyi_sale_order_line c on c.order_id = a.id inner join
                        public.ziyi_product d on d.id = c.product_id left join 
                        public.res_users f on f.id = a.create_uid left join 
                        (
                            select  min(plan_date) as plan_date, line_id
                            from    public.ziyi_sale_order_line_batch
                            group by line_id 
                        ) as g on g.line_id = c.id
                where   c.write_date > CURRENT_TIMESTAMP - INTERVAL '{time_interval}' 
                order by a.id asc
                limit {QUERY_LIMIT}
            """

    results = db.execute_query(query)

    if not results:
        logger.info("没有订单资料")
        return 
        
    list_value = []
    list_bom_value = []
    
    for res in results:
        try:
            # 处理单个订单
            order_json, json_bom = process_single_order(db, res)
            if order_json :
                list_value.append(order_json)
            if json_bom:
                list_bom_value.append(json_bom)
        except Exception as e:
            logger.error(f"处理订单 {res.get('contract_no', '未知')} 时发生错误: {e}")
            continue
    
    logger.info(f"共处理 {len(list_value)} 个订单")
    return list_value, list_bom_value


def process_single_order(db, res):
    """处理单个订单数据"""
    try :
    # 订单明细
        itemList = []
        query_order_line = """
                            select  a.color_id , b.name as color_name, b.code as color_code, c.name as size_name, c.code as size_code, 
                                    a.line_id , a.value , a.price , a.product_id , a.batch_date , a.batch_name
                            from    public.ziyi_sale_order_line_batch_quantity_size a inner join
                                    public.ziyi_base_color b on b.id = a.color_id inner join 
                                    public.ziyi_base_size c on c.id = a.size_id 
                            where   a.line_id = %s 
                            order by a.color_id , a.size_id
                          """
        
        results_order_line = db.execute_query(query_order_line, [res['order_line_id']])

        if not results_order_line:
            logger.warning(f"订单行 {res['order_line_id']} 没有明细数据")
            return 
    
        color_id = ""
        colorerpid = 0

        for res_line in results_order_line:
            if color_id != res_line['color_id']:
                colorerpid += 1
                color_id = res_line['color_id']
            item_json = {
                'colorErpId': colorerpid,  # 序号
                'colorCode': res_line['color_code'],
                'colorName': res_line['color_name'],
                'deliveryDate': res_line['batch_date'].strftime("%Y-%m-%d"),  # 交货日期
                'po': res_line['batch_name'],  # 取批次名称
                'qty': res_line['value'],
                'sizeCode': res_line['size_name'],
                'sizeName': res_line['size_name'],
                'outBarCode': ""
            }
            itemList.append(item_json)

        # 订单头
        billno = f"{res['contract_no']}_{res['itemcode']}"
        order_json = {
            'billNo': billno,  # 生产单号(必填)
            'customerCode': res['cuscode'],  # 客户编码(必填)
            'customerName': res['cusname'],  # 客户名称
            'depotDeliveryDate': res['plan_date'].strftime("%Y-%m-%d") if res['plan_date'] else "",  # 出厂日期
            'createTime': res['create_date'].strftime("%Y-%m-%d %H:%M:%S"),  # 创建时间
            'creater': res['creater'],  # 创建人
            'state': 1,  # 状态 (0:未审核；1:已审核；2，已作废；3，已结案) 默认1
            'itemCode': res['itemcode'],  # 款号(必填)
            'itemList': itemList  # 订单明细(必填)
        }

        # 订单BOM
        json_bom = process_order_bom(db, res, billno)       
        return order_json, json_bom

    except Exception as e:
        logger.error(f"查询订单行失败: {e}")
        return None, None
        

def process_order_bom(db, res, billno):
    """处理订单BOM数据"""
    try:
        # 查询款式BOM
        results_bom = get_product_bom(db, res['product_id'])
        if not results_bom:
            logger.warning(f"{res['itemcode']}款号没有BOM资料！")
            return None
            
        fabricBOMList = []
        accessoryBOMList = []
        
        for res_bom in results_bom:
            # 处理单个BOM物料
            material_json, material_type = process_single_bom_material(db, res_bom)
            
            if material_type == 'B':  # 面料
                fabricBOMList.append(material_json)
            elif material_type == 'F':  # 辅料
                accessoryBOMList.append(material_json)

        if not fabricBOMList and not accessoryBOMList:
            logger.warning(f"订单 {billno} 的款式{res['itemcode']} BOM中没有面料或辅料！不写入BOM")
            return
        # 写入mes接口款式BOM
        json_bom = {
            "orderNo": billno,
            "fabricBOMList": fabricBOMList,
            "accessBOMList": accessoryBOMList,
        }
        return json_bom
        
    except Exception as e:
        logger.error(f"处理订单BOM时发生错误: {e}")
        return None


def process_single_bom_material(db, res_bom):
    """处理单个BOM物料数据"""
    matecolorlist = []
    matesizelist = []
    matecolorpricelist = []

    # 1. 物料规格
    query_bom_spec = ''' 
                    select  t.id , t.value , t.quantity , b.name  
                    from	(
                                select  bom.id , bom.quantity , COALESCE(a.size_id , pz.size_id) as size_id , COALESCE(a.value , bom.common_spec) as value
                                from	public.ziyi_product_bom bom inner join 
                                        public.ziyi_relation_product_size pz on pz.product_id = bom.product_id left join 
                                        public.ziyi_product_bom_size a on bom.id = a.parent_id and a.size_id = pz.size_id 
                                where 	bom.id = %s
                            ) t 
                            inner join public.ziyi_base_size b on b.id = t.size_id 
                    order by t.id asc, b.sequence asc
                '''
    results_bom_spec = db.execute_query(query_bom_spec, [res_bom['bom_id']])       
    dis_specList = []
    bom_size_value = ""
    
    for res_bom_spec in results_bom_spec:
        spec_json = {
            'sizeCode': res_bom_spec['name'] , 
            'sizeName': res_bom_spec['name'] ,  # 尺码名称
            'model': res_bom_spec['value'] ,    # 物料规格
            'qty': str(res_bom_spec['quantity']),   # 物料用量
        }
        matesizelist.append(spec_json)
        # 写入规格
        if res_bom_spec['value'] not in dis_specList:
            dis_specList.append(res_bom_spec['value'])
        if not bom_size_value:
            bom_size_value = res_bom_spec['value']
    # 如果没有规格则取通配规格
    # 2. 物料颜色
    query_bom_color = ''' 
                        select  t.id , b.name as itemcolorname, b.code as itemcolorcode, c.name as colorname, c.code as colorcode , t.value
                        from	(
                                    select  bom.id , COALESCE(a.color_id , pc.color_id) as color_id , COALESCE(a.value , bom.common_color) as value
                                    from	public.ziyi_product_bom bom inner join 
                                            public.ziyi_relation_product_color pc on pc.product_id = bom.product_id left join 
                                            public.ziyi_product_bom_color a on bom.id = a.parent_id 
                                    where 	bom.id = %s
                                ) t 
                                inner join public.ziyi_base_color b on b.id = t.color_id 
                                inner join public.ziyi_base_color c on c.id = t.value
                        order by t.id asc 
                    '''
    
    results_bom_color = db.execute_query(query_bom_color, [res_bom['bom_id']])
        
    for res_bom_color in results_bom_color:
        color_json = {
            'orderColorCode': res_bom_color['itemcolorcode'], # 成品色号    
            'orderColorName': res_bom_color['itemcolorname'], # 成品颜色    
            'colorCode': res_bom_color['colorcode'] ,
            'colorName': res_bom_color['colorname'] ,
            'model' : bom_size_value,   # 物料规格    
            'price' : float(str(res_bom['price'])),   # 单价    
            'wastRate': 0, # 损耗率    
            'sizeQty' : 0, # 用量    
            'remark'  : '', # 备注    
        }
        matecolorlist.append(color_json)

        # 3. 物料颜色价格 - 检查dis_specList是否为空
        if dis_specList:
            query_bom_color_price = ''' 
                                select  distinct price , name
                                from    public.ziyi_base_material_details
                                where   material_id = %s and color_id = %s and name in %s
                                limit 1                        
                            '''

            results_bom_color_price = db.execute_query(
                query_bom_color_price, 
                (res_bom['material_id'], res_bom_color['value'], tuple(dis_specList))
            )
                
            for color_price in results_bom_color_price:
                color_price_json = {
                    "colorCode": res_bom_color['colorcode'] ,
                    "colorName": res_bom_color['colorname'] ,
                    "model": color_price['name'] , # 物料规格
                    "price": float(str(color_price['price'])),
                }
                matecolorpricelist.append(color_price_json)

    # 提取克重字符串的数值
    weight = extract_single_weight(res_bom['weight'])
    material_json = {
        'mateCode': res_bom['code'],
        'mateName': res_bom['name'],
        'mateUnit': res_bom['mate_unit'],       # 物料单位
        'mateSource': res_bom['matesource'] ,   # 物料来源
        'providerCode': res_bom['supplier_code'], # 供应商编码
        'providerName': res_bom['supplier_name'], # 供应商名称
        'price': float(str(res_bom['price'])),              # 单价
        'element': res_bom['composition'],      # 成分
        'wastRate': 0,                          # 损耗率 成衣损耗  默认0
        'unit': res_bom['unit'] or res_bom['mate_unit'],  # 物料转换单位
        'model': bom_size_value,                # 物料规格
        'weight': weight,                       # 克重数值
        'part': res_bom['part'],                # 部位
        'termType': 1,                          # 期限类型： 1 前期物料；2 中期物料；3 后期物料
        'remarks': res_bom['memo'] ,
        'mateColorList': matecolorlist,
        'mateSizeList': matesizelist,
        'mateColorPriceList': matecolorpricelist
    }
    return material_json, res_bom['type_code']


def send_orders_to_api(baseURL, str_token, orders_data, boms_data):
    """发送订单和BOM数据到API"""
    headers = {
        "Content-Type": "application/json",
        "smagar-token": str_token
    }
    
    # 发送生产订单数据
    if orders_data:
        try:
            url = f"{baseURL}{API_ENDPOINT}"
            logger.info(f"发送生产订单数据到: {url}")
            logger.info(f"订单数据: {orders_data}")
            response = requests.post(url, headers=headers, json=orders_data, timeout=30)
            response.raise_for_status()
            logger.info(f"生产订单发送成功: {response.json()}")
            
        except Exception as e:
            logger.error(f"发送生产订单失败: {e}")
            return
            
        # 发送BOM数据
        for i, bom_data in enumerate(boms_data):
            try:
                url_bom = f"{baseURL}{API_ENDPOINT_BOMS}"
                order_no = bom_data.get('orderNo', f'未知订单_{i}')
                logger.info(f"发送BOM数据: {order_no}")
                logger.info(f"BOM数据: {bom_data}")
                response_bom = requests.post(url_bom, headers=headers, json=bom_data, timeout=30)
                response_bom.raise_for_status()
                logger.info(f"BOM发送成功: {response_bom.json()}")
            except Exception as e:
                logger.error(f"发送BOM失败 ({order_no}): {e}")
                continue


if __name__ == "__main__":
    main()