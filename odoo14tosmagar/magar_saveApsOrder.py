import requests
import logging
from get_conf import Config
from magar_smanager_token import MES_Get_token
from odoo_db_con import PostgreSQLConnector
from funcs import get_product_bom, extract_single_weight

logger = logging.getLogger(__name__)

def main():
    
    try:
        # mes 配置
        config = Config()
        baseURL = config.baseURL
        appkey = config.appkey
        appSecret = config.appSecret
        # postgresql 配置
        host = config.host
        port = config.port
        database = config.database
        username = config.username
        password = config.password
        
    except FileNotFoundError as e:
        print(f"错误: {e}")
    
    # 获取mes接口token
    token = MES_Get_token(baseURL, appkey, appSecret)
    str_token = token.get_token()

    db = PostgreSQLConnector(host, port, database, username, password)
    print("\n开始查询订单: ")
    query = """
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
                            from	public.ziyi_sale_order_line_batch
                            group by line_id 
                        ) as g on g.line_id = c.id
                where   c.write_date > CURRENT_TIMESTAMP - INTERVAL '3 HOURS'
                order by a.id asc
                limit 50
            """

    results = db.execute_query(query)
    list_value = []
    list_bom_value = []
    order_line_id_list = [] # 为了
    if not results :
        print("没有订单资料")
        return
    for res in results:
        # 订单明细
        itemList = []
        query_order_line = """
                            select  a.color_id , b.name as color_name, b.code as color_code, c.name as size_name, c.code as size_code, 
                                    a.line_id , a.value , a.price , a.total_price , a.product_id , a.batch_date , a.batch_name
                            from	public.ziyi_sale_order_line_batch_quantity_size a inner join
                                    public.ziyi_base_color b on b.id = a.color_id inner join 
                                    public.ziyi_base_size c on c.id = a.size_id 
                            where   a.line_id = %s 
                            order by a.color_id , a.size_id
                            """
        results_order_line = db.execute_query(query_order_line, [res['order_line_id']])
        color_id = ""
        colorerpid = 0
        for res_line in results_order_line:
            if color_id != res_line['color_id']:
                colorerpid += 1
                color_id = res_line['color_id']
            item_json = {
                'colorErpId': colorerpid,
                'colorCode': res_line['color_code'],
                'colorName': res_line['color_name'],
                'deliver' : res_line['batch_date'].strftime("%Y/%m/%d"), # 交货日期
                'po': res_line['batch_name'],  # 取批次名称
                'qty': res_line['value'],
                'sizeCode': res_line['size_name'],
                'sizeName': res_line['size_name'],
                'outBarCode': ""
            }
            itemList.append(item_json)
        print('itemlist %s',itemList)
        # 1. 订单头
        billno = res['contract_no'] + "_" + res['itemcode']
        json = {
            'billNo': billno, # 生产单号(必填)
            'customerCode': res['cuscode'],  # 客户编码(必填)
            'customerName': res['cusname'], # 客户名称
            'depotDeliveryDate': res['plan_date'].strftime("%Y-%m-%d"),  # 出厂日期 (yyyy-MM-dd，必填) 取批次交期中的计划交期，先取最小值
            'createTime': res['create_date'].strftime("%Y-%m-%d %H:%M:%S"),  # 创建时间
            'creater': res['creater'], # 先默认写管理员
            'state':1, # 状态 (状态：0:未审核；1:已审核；2，已作废；3，已结案) 默认1
            'itemCode': res['itemcode'], # 款号(必填)
            'itemList': itemList  # 订单明细(必填)
        }

        #-------------------------------------------------------------------------------#
        # 2. 订单BOM
        order_line_id_list.append(res['order_line_id'])
        
        # 2.1 查询款式BOM
        results_bom = get_product_bom(db, res['product_id'], res['itemcode'])
        if not results_bom:
            print(res['itemcode']+"款号没有BOM资料！")
            continue
        fabricBOMList = []
        accessoryBOMList = []
        for res_bom in results_bom:
            matecolorlist = []
            matesizelist = []
            matecolorpricelist = []
            pocolorlist = []

            # 1. 物料规格
            query_bom_spec = """ 
                                select  base_size.name , base_size.code , bom_size.value , bom.quantity
                                from	public.ziyi_product_bom_size bom_size inner join 
                                        public.ziyi_base_size base_size on base_size.id = bom_size.size_id inner join 
                                        public.ziyi_product_bom bom on bom.id = bom_size.parent_id
                                where   bom.id = %s
                                order by parent_id asc , base_size.sequence asc
                            """
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
                if res_bom_spec['value'] not in dis_specList:
                    dis_specList.append(res_bom_spec['value'])
                if not bom_size_value:
                    bom_size_value = res_bom_spec['value']

            # 2. 物料颜色
            query_bom_color = """ 
                                select  b.name as itemcolorname , b.code as itemcolorcode , c.name as colorname , c.code as colorcode , a.value
                                from    ziyi_product_bom_color a inner join 
                                        ziyi_base_color b on b.id = a.color_id inner join 
                                        ziyi_base_color c on c.id = a.value 
                                where   parent_id = %s 
                                order by a.id asc
                            """
            results_bom_color = db.execute_query(query_bom_color, [res_bom['bom_id']])
            for res_bom_color in results_bom_color:
                color_json = {
                    'orderColorCode': res_bom_color['itemcolorcode'],	# 成品色号	款式色号？？
                    'orderColorName': res_bom_color['itemcolorname'],	# 成品颜色	
                    'colorCode': res_bom_color['colorcode'] ,
                    'colorName': res_bom_color['colorname'] ,
                    'model'	: bom_size_value,   # 物料规格	是  多规格，取第一个？？
                    'price'	: str(res_bom['price']),   # 单价	是  取哪个单价？
                    'wastRate':	0, # 损耗率	是
                    'sizeQty' :	0, # 用量	是
                    'remark'  :	'', # 备注	
                }
                matecolorlist.append(color_json)	

                # 3. 物料颜色价格
                query_bom_color_price = """ 
                                        select  distinct price , name
                                        from    public.ziyi_base_material_details
                                        where   material_id = %s and color_id = %s and name in %s
                                        --order by id asc 
                                        limit 1                       
                                    """
                results_bom_color_price = db.execute_query(query_bom_color_price, ([res_bom['material_id'], res_bom_color['value'], tuple(dis_specList)]))
                # print(f"results_bom_color_price: {results_bom_color_price}")
                for color_price in results_bom_color_price:
                    color_price_json = {
                        "colorCode": res_bom_color['colorcode'] ,
                        "colorName": res_bom_color['colorname'] ,
                        "model": color_price['name'] , # 物料规格
                        "price": str(color_price['price'])
                    }
                matecolorpricelist.append(color_price_json)

            # 提取克重字符串的数值
            weight = extract_single_weight(res_bom['weight'])
            material_json={
                            'mateCode': res_bom['code'],
                            'mateName': res_bom['name'],
                            'mateUnit': res_bom['mate_unit'],       # 物料单位
                            'mateSource': res_bom['matesource'] ,   # 物料来源 (必填;1，采购；2，加工；3，客供) 加工是外包
                            'providerCode': res_bom['supplier_code'], # 供应商编码
                            'providerName': res_bom['supplier_name'], # 供应商名称
                            'price': str(res_bom['price']),              # 单价
                            'element': res_bom['composition'],      # 成分
                            'wastRate': 0,                          # 损耗率 成衣损耗  默认0
                            'unit': res_bom['unit'] or res_bom['mate_unit'],  # 物料转换单位
                            'model': bom_size_value,                # 多规格，取哪个？ 先取第一个规格
                            'weight': weight,                       # 取字符串中的第一个数值
                            'part': res_bom['part'],                # 部位
                            'mateSource': res_bom['matesource'] ,   # 物料来源 (必填;1，采购；2，加工；3，客供) 加工是外包,
                            'termType': 1,                          #??? 期限类型： 1 前期物料；2 中期物料；3 后期物料
                            'remarks': res_bom['memo'] ,
                            'mateColorList': matecolorlist,
                            'mateSizeList': matesizelist,
                            'mateColorPriceList': matecolorpricelist
                            # 'poColorList': pocolorlist
                            }
            
            if res_bom['type_code'] == 'B':  # 面料
                fabricBOMList.append(material_json)
            elif res_bom['type_code'] == 'F':  # 辅料
                accessoryBOMList.append(material_json)    

        json_bom = {
            "orderNo": billno,
            "fabricBOMList": fabricBOMList,
            "accessBOMList": accessoryBOMList,
            }

        # 订单表头信息list   
        list_value.append(json)

        # 订单BOM
        list_bom_value.append(json_bom)
    # 写入mes接口  生产订单
    url = Config().baseURL + "/yzApi/saveApsOrder"
    # 写入mes接口
    url_bom = Config().baseURL + "/yzApi/saveApsOrderBoms"

    headers = {
        "Content-Type": "application/json",
        "smagar-token": str_token
    }
    print(f"url: {url}")
    # print(f"json: {json}")
    response = requests.post(url, headers=headers, json=list_value)
    print(response.json())
    
    print(f"url_bom: {url_bom}")
    # print(f"json_bom:{json_bom}")
    # 循环 list_bom_value
    for j in range(len(list_bom_value)):
        list_bom_value[j]
        print(list_bom_value[j])
        response_bom = requests.post(url_bom, headers=headers, json=list_bom_value[j])
        print(response_bom.json())


if __name__ == "__main__":
    main()