import requests
import re
from get_conf import Config
from magar_smanager_token import MES_Get_token
from odoo_db_con import PostgreSQLConnector
from funcs import get_product_bom, extract_single_weight

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
    print("\n开始查询款式资料: ")
    query = """
                SELECT  a.id as product_id , a.name , a.design_no , b.name as unit , c.name as year , 
                        d.name as season , e.name as brand , f.name as designer, 
                        g.name as stylename, g.code as stylecode, h.name as wave, a.memo as remark
                FROM    ziyi_product a inner join 
                        ziyi_base_unit b on b.id = a.unit_id left join 
                        ziyi_base_year c on c.id = a.year_id left join 
                        ziyi_base_season d on d.id = a.season_id left join 
                        ziyi_base_partner e on e.id = a.partner_id left join 
                        ziyi_base_employee f on f.id = a.designer_id left join 
                        ziyi_base_style g on g.id = a.style_id left join 
                        ziyi_base_season_batch h on h.id = a.season_batch_id
                WHERE   a.active = true and
                        a.write_date > CURRENT_TIMESTAMP - INTERVAL '6 HOURS' LIMIT 500
    """
    results = db.execute_query(query)
    if not results:
        print("没有款式资料")
        return
    # 注意：mes款式不支持批量写入，每次只能写入一个款式
    for res in results:
        # 款式SKU color
        # query_sku = """
        #             select  a.id as product_id, c.id as color_id, e.id as size_id, c.name as colorname, c.code as colorcode , e.name as sizename, e.code as sizecode
        #             from    ziyi_product a inner join 
        #                     ziyi_relation_product_color b on b.product_id = a.id inner join 
        #                     ziyi_base_color c on c.id = b.color_id inner join 
        #                     ziyi_relation_product_size d on d.product_id = a.id inner join 
        #                     ziyi_base_size e on e.id = d.size_id 
        #             where   a.id = %s
        #             order by a.id , c.id , e.id   
        #             """
        # results_sku = db.execute_query(query_sku, (res['product_id'],))
        # list_sku = []
        # for res_sku in results_sku:
        #     sku_json = {
        #         'colorCode': res_sku['colorcode'] ,
        #         'colorName': res_sku['colorname'] ,
        #         'sizeCode': res_sku['sizecode'] or res_sku['sizename'] ,
        #         'sizeName': res_sku['sizename'] ,
        #         'outBarcode': ''
        #     }
        #     list_sku.append(sku_json)
        # 款式颜色
        query_color = """
                        select  a.id as product_id, c.id as color_id, c.name as colorname, c.code as colorcode
                        from    ziyi_product a inner join 
                                ziyi_relation_product_color b on b.product_id = a.id inner join 
                                ziyi_base_color c on c.id = b.color_id                                 
                        where   a.id = %s
                        order by a.id , c.id asc
                    """
        results_color = db.execute_query(query_color, (res['product_id'],))
        if not results_color :
            print("没有颜色资料！")
            continue
        color_list = []
        for res_color in results_color:
            color_json = {
                'colorCode': res_color['colorcode'] ,
                'colorName': res_color['colorname'] ,
                'orderId': len(color_list) + 1 ,
                'state': 1 
            }
            color_list.append(color_json)

        # 款式尺码
        query_size = """
                        select  a.id as product_id, e.id as size_id, e.name as sizename , f.name as categoryname
                        from    ziyi_product a inner join
                                ziyi_relation_product_size d on d.product_id = a.id inner join 
                                ziyi_base_size e on e.id = d.size_id left join 
                                ziyi_base_category f on f.id = e.category_id
                        where   a.id = %s
                        order by a.id , e.sequence   
                    """
        results_size = db.execute_query(query_size, (res['product_id'],))
        size_list = []
        categoryname = "" # 尺码组名称
        if not results_size :
            print("没有尺码资料！")
            continue
        if results_size[0]['categoryname']:
            categoryname = results_size[0]['categoryname']
        for res_size in results_size:

            size_json = {
                'sizeCode': res_size['sizename'] ,
                'sizeName': res_size['sizename'] ,
                'orderId': len(size_list) + 1 ,
                'state': 1 
            }
            size_list.append(size_json)
        json = {	
                'code' : res['design_no'],	#款号	是
                'name' : res['name'],	#品名	是
                'sizeCode': "",	#尺码组编码	
                'sizeName': categoryname,	#尺码组名称	是
                'categoryCode':res['stylecode'],	#分类编码	取系列款式分类
                'categoryName':res['stylename'],	#分类名称	取系列款式分类
                'unit' : res['unit'],	#单位	
                'year' : res['year'],	#年份	
                'season' : res['season'],	#季节	
                'brand' : res['brand'],	#品牌	
                'designer' : res['designer'],	#设计师	是
                'creater' : "",	#创建人	是
                'createDate' : "",	#创建时间	是
                # 'styleName'	: ,	#款式风格	
                'sex': "/",	#性别 odoo14中没有性别字段 , 需要增加字段
                'wave': res['wave'],	#波段	
                'customerItem': res['design_no'],	#客户款号	取设计款号
                'state'	: 1 ,#状态 1	是
                'remark': res['remark'],	#备注	
                'colorList': color_list,	#款式颜色列表
                'sizeList':size_list,	#款式尺码列表
                # "skuList": list_sku,
                }
        print(json)

        # 写入mes接口
        url = Config().baseURL + "/yzApi/saveBaItem"
        headers = {
            "Content-Type": "application/json",
            "smagar-token": str_token
        }
        print(f"url: {url}")
        response = requests.post(url, headers=headers, json=json)
        print(response.json())

        # 款式BOM接口
        print("\n开始查询款式BOM: 先暂时认为小于30个物料")
        # 获取物料BOM
        # query_bom = """
        #             select  b.design_no , 
        #                     c.name , c.code , c.composition , c.package_transform , c.price , c.weight , 
        #                     e.name as mate_unit , 
        #                     a.id as bom_id , d.code as type_code , a.quantity , a.unit_loss , a.memo , a.material_id ,
        #                     f.code as supplier_code,
        #                     f.name as supplier_name,
        #                     g.name as unit ,
        #                     i.name as part ,
        #                     case h.code when 'M1' then 1 when 'M2' then 3 when 'M3' then 2 when 'M4' then 2 else 1 end as matesource
        #             from    public.ziyi_product_bom a inner join 
        #                     public.ziyi_product b on b.id = a.product_id inner join 
        #                     public.ziyi_base_material c on c.id = a.material_id inner join 
        #                     public.ziyi_base_material_type d on d.id = c.type_id left join 
        #                     public.ziyi_base_unit e on e.id = c.unit_id left join 
        #                     public.ziyi_base_partner f on f.id = c.supplier_id left join 
        #                     public.ziyi_base_unit g on g.id = c.min_package_unit_id left join 
        #                     public.ziyi_base_supplier_type h on h.id = a.supplier_type_id left join 
        #                     public.ziyi_base_parts i on i.id = a.parts_id
        #             WHERE   a.active = true and b.active = true and 
        #                     b.id = %s and d.code in ('B','F')
        #                     --a.write_date > CURRENT_TIMESTAMP - INTERVAL '6 HOURS' 
        #             order by d.id , a.sequence , a.id 
        #             LIMIT 30
        #         """
        # results_bom = db.execute_query(query_bom, [res['product_id']]) 
        results_bom = get_product_bom(db, res['product_id'], res['itemcode'])
        if not results_bom:
            print(res['itemcode']+"款号没有BOM资料！")
            continue
        
        # print(f"results_bom: {results_bom}")
        fabricBOMList = []
        accessoryBOMList = []
        for res_bom in results_bom:
            material_json = {}
            colorList = []
            matesizelist = []
            matecolorpricelist = []

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
                    'sizeName': res_bom_spec['name'] ,
                    'model': res_bom_spec['value'] ,
                    'qty': str(res_bom_spec['quantity'])
                }
                matesizelist.append(spec_json)
                if res_bom_spec['value'] not in dis_specList:
                    dis_specList.append(res_bom_spec['value'])
                if not bom_size_value:
                    bom_size_value = res_bom_spec['value']
            # print(specList)

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
                    'itemColorCode': res_bom_color['itemcolorcode'] ,
                    'itemColorName': res_bom_color['itemcolorname'] ,
                    'colorCode': res_bom_color['colorcode'] ,
                    'colorName': res_bom_color['colorname'] ,
                    'mateSizeList': matesizelist  # 物料规格
                }
                colorList.append(color_json)
               
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
            # print(matecolorpricelist)
            # 提取克重字符串的数值
            weight = extract_single_weight(res_bom['weight'])

            material_json = {
                    'mateCode': res_bom['code'] ,
                    'mateName': res_bom['name'] ,
                    'mateUnit': res_bom['mate_unit'],       # 物料单位
                    'mateSource': res_bom['matesource'] ,   # 物料来源 (必填;1，采购；2，加工；3，客供) 加工是外包
                    'unit': res_bom['unit'] or res_bom['mate_unit'],  # 物料转换单位
                    'providerCode': res_bom['supplier_code'] , # 供应商编码
                    'providerName': res_bom['supplier_name'] , # 供应商名称
                    'price': str(res_bom['price']),              # 单价
                    'element': res_bom['composition'],      # 成分
                    # 'unitRate': float(res_bom['package_transform']),  # 系数
                    "model": bom_size_value,                # 多规格，取哪个？ 先取第一个规格
                    'weight': weight,                       # odoo14是char类型，取字符串中的第一个数值
                    'wastRate': 0,                          # 损耗率 是成衣损耗，先默认0
                    'part': res_bom['part'],                # 部位
                    'mate5ource': 1,
                    'remarks': res_bom['memo'] ,
                    'colorList': colorList,                 # 物料配色
                    'mateSizeList': matesizelist,           # 物料配码
                    'mateColorPriceList': matecolorpricelist  # 物料单价
                }
            if res_bom['type_code'] == 'B':  # 面料
                fabricBOMList.append(material_json)
            elif res_bom['type_code'] == 'F':  # 辅料
                accessoryBOMList.append(material_json)    
        
        # 写入mes接口款式BOM
        json_bom = {
            'itemCode': res['design_no'],
            'fabricBOMList': fabricBOMList,
            'accessBOMList': accessoryBOMList
        }
        url_bom = Config().baseURL + "/yzApi/saveBaItemBoms"
        headers = {
            'Content-Type': "application/json",
            'smagar-token': str_token
        }
        print(f"url_bom: {url_bom}")
        # print(f"json_bom: {json_bom}")
        response_bom = requests.post(url_bom, headers=headers, json=json_bom)
        print(response_bom.json())

    db.close()

if __name__ == "__main__":
    main()