import requests
import re
import logging
from get_conf import Config
from odoo_db_con import get_db_connection
from funcs import get_product_bom, extract_single_weight

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 常量定义
TIME_INTERVAL = '6 HOURS'
QUERY_LIMIT = 500
MAX_BOM_MATERIALS = 30
API_ITEM_ENDPOINT = '/yzApi/saveBaItem'
API_BOM_ENDPOINT = '/yzApi/saveBaItemBoms'


def main():
    str_token = ""
    db = None
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
        
    try:
            
        # 获取数据库连接
        db = get_db_connection(config)  
        logger.info("开始查询款式资料")
        
        # 构造查询语句
        query = f"""
                    SELECT  a.id as product_id, a.name, a.design_no, b.name as unit, c.name as year,
                            d.name as season, e.name as brand, f.name as designer,
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
                            a.write_date > CURRENT_TIMESTAMP - INTERVAL '{TIME_INTERVAL}' 
                    LIMIT {QUERY_LIMIT}
        """
        
        results = db.execute_query(query)
        
        if not results:
            logger.info("没有款式资料")
            return
            
        # 注意：mes款式不支持批量写入，每次只能写入一个款式
        for res in results:
            process_single_item(db, baseURL, str_token, res)
            
    except requests.exceptions.RequestException as e:
        logger.error(f"API请求失败: {e}")
    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}")
    finally:
        # 确保数据库连接关闭
        if db and hasattr(db, 'close'):
            try:
                db.close()
            except Exception as e:
                logger.error(f"关闭数据库连接时发生错误: {e}")


def process_single_item(db, baseURL, str_token, res):
    """处理单个款式数据"""
    try:
        # 款式颜色
        query_color = """
                        select  a.id as product_id, c.id as color_id, c.name as colorname, c.code as colorcode
                        from    ziyi_product a inner join
                                ziyi_relation_product_color b on b.product_id = a.id inner join
                                ziyi_base_color c on c.id = b.color_id                                 
                        where   a.id = %s
                        order by a.id, c.id asc
                    """
        results_color = db.execute_query(query_color, (res['product_id'],))
        
        if not results_color:
            logger.warning(f"款号 {res['design_no']} 没有颜色资料！")
            return
            
        color_list = []
        for res_color in results_color:
            color_json = {
                'colorCode': res_color['colorcode'],
                'colorName': res_color['colorname'],
                'orderId': len(color_list) + 1,
                'state': 1
            }
            color_list.append(color_json)

        # 款式尺码
        query_size = """
                        select  a.id as product_id, e.id as size_id, e.name as sizename, f.name as categoryname
                        from    ziyi_product a inner join
                                ziyi_relation_product_size d on d.product_id = a.id inner join
                                ziyi_base_size e on e.id = d.size_id left join
                                ziyi_base_category f on f.id = e.category_id
                        where   a.id = %s
                        order by a.id, e.sequence   
                    """
        results_size = db.execute_query(query_size, (res['product_id'],))
        
        if not results_size:
            logger.warning(f"款号 {res['design_no']} 没有尺码资料！")
            return
            
        size_list = []
        categoryname = results_size[0]['categoryname'] or ""
        
        for res_size in results_size:
            size_json = {
                'sizeCode': res_size['sizename'],
                'sizeName': res_size['sizename'],
                'orderId': len(size_list) + 1,
                'state': 1
            }
            size_list.append(size_json)
            
        # 构造款式数据
        item_data = {
            'code': res['design_no'],       #款号
            'name': res['name'],            #品名
            'sizeCode': "",                #尺码组编码
            'sizeName': categoryname,       #尺码组名称
            'categoryCode': res['stylecode'], #分类编码
            'categoryName': res['stylename'], #分类名称
            'unit': res['unit'],            #单位
            'year': res['year'],            #年份
            'season': res['season'],        #季节
            'brand': res['brand'],          #品牌
            'designer': res['designer'],    #设计师
            'creater': "",                  #创建人
            'createDate': "",               #创建时间
            'sex': "/",                     #性别
            'wave': res['wave'],            #波段
            'customerItem': res['design_no'], #客户款号
            'state': 1,                     #状态 1
            'remark': res['remark'],        #备注
            'colorList': color_list,        #款式颜色列表
            'sizeList': size_list,          #款式尺码列表
        }
        
        logger.debug(f"准备的款式数据: {item_data}")
        
        # 写入mes接口
        url = f"{baseURL}{API_ITEM_ENDPOINT}"
        headers = {
            "Content-Type": "application/json",
            "smagar-token": str_token
        }
        
        logger.info(f"开始写入款式资料: {res['design_no']}")
        response = requests.post(url, headers=headers, json=item_data, timeout=60)
        response.raise_for_status()
        
        logger.info(f"款式写入响应: {response.json()}")
        
        # 处理款式BOM
        process_item_bom(db, baseURL, str_token, res)
        
    except Exception as e:
        logger.error(f"处理款式 {res.get('design_no', '未知')} 时发生错误: {e}")


def process_item_bom(db, baseURL, str_token, res):
    """处理款式BOM数据"""
    try:
        logger.info(f"开始查询款式BOM: {res['design_no']}")
        
        # 获取物料BOM
        results_bom = get_product_bom(db, res['product_id'], res['design_no'])
        
        if not results_bom:
            logger.warning(f"款号 {res['design_no']} 没有BOM资料！")
            return
            
        fabricBOMList = []
        accessoryBOMList = []
        
        for res_bom in results_bom:
            # 处理单个BOM物料
            material_json, material_type = process_single_bom_material(db, res_bom)
            
            if material_type == 'B':  # 面料
                fabricBOMList.append(material_json)
            elif material_type == 'F':  # 辅料
                accessoryBOMList.append(material_json)
                
        # 写入mes接口款式BOM
        json_bom = {
            'itemCode': res['design_no'],
            'fabricBOMList': fabricBOMList,
            'accessBOMList': accessoryBOMList
        }
        
        url_bom = f"{baseURL}{API_BOM_ENDPOINT}"
        headers = {
            'Content-Type': "application/json",
            'smagar-token': str_token
        }
        
        logger.info(f"开始写入款式BOM: {res['design_no']}")
        response_bom = requests.post(url_bom, headers=headers, json=json_bom, timeout=60)
        response_bom.raise_for_status()
        
        logger.info(f"BOM写入响应: {response_bom.json()}")
        
    except Exception as e:
        logger.error(f"处理款式 {res['design_no']} BOM时发生错误: {e}")


def process_single_bom_material(db, res_bom):
    """处理单个BOM物料数据"""
    colorList = []
    matesizelist = []
    matecolorpricelist = []

    # 1. 物料规格
    query_bom_spec = """ 
                    select  base_size.name, base_size.code, bom_size.value, bom.quantity
                    from    public.ziyi_product_bom_size bom_size inner join
                            public.ziyi_base_size base_size on base_size.id = bom_size.size_id inner join
                            public.ziyi_product_bom bom on bom.id = bom_size.parent_id
                    where   bom.id = %s
                    order by parent_id asc, base_size.sequence asc
                    """
    results_bom_spec = db.execute_query(query_bom_spec, [res_bom['bom_id']])
    dis_specList = []
    bom_size_value = ""
    
    for res_bom_spec in results_bom_spec:
        spec_json = {
            'sizeCode': res_bom_spec['name'],
            'sizeName': res_bom_spec['name'],
            'model': res_bom_spec['value'],
            'qty': str(res_bom_spec['quantity'])
        }
        matesizelist.append(spec_json)
        
        if res_bom_spec['value'] not in dis_specList:
            dis_specList.append(res_bom_spec['value'])
        
        if not bom_size_value:
            bom_size_value = res_bom_spec['value']

    # 2. 物料颜色
    query_bom_color = """ 
                    select  b.name as itemcolorname, b.code as itemcolorcode, c.name as colorname, c.code as colorcode, a.value
                    from    ziyi_product_bom_color a inner join
                            ziyi_base_color b on b.id = a.color_id inner join
                            ziyi_base_color c on c.id = a.value
                    where   parent_id = %s
                    order by a.id asc
                    """
    results_bom_color = db.execute_query(query_bom_color, [res_bom['bom_id']])
    
    for res_bom_color in results_bom_color:
        color_json = {
            'itemColorCode': res_bom_color['itemcolorcode'],
            'itemColorName': res_bom_color['itemcolorname'],
            'colorCode': res_bom_color['colorcode'],
            'colorName': res_bom_color['colorname'],
            'mateSizeList': matesizelist  # 物料规格
        }
        colorList.append(color_json)
        
        # 3. 物料颜色价格
        query_bom_color_price = """
                                select  distinct price, name
                                from    public.ziyi_base_material_details
                                where   material_id = %s and color_id = %s and name in %s
                                limit 1                       
                            """
        results_bom_color_price = db.execute_query(
            query_bom_color_price, 
            ([res_bom['material_id'], res_bom_color['value'], tuple(dis_specList)])
        )
        
        for color_price in results_bom_color_price:
            color_price_json = {
                "colorCode": res_bom_color['colorcode'],
                "colorName": res_bom_color['colorname'],
                "model": color_price['name'], # 物料规格
                "price": str(color_price['price'])
            }
            matecolorpricelist.append(color_price_json)
    
    # 提取克重字符串的数值
    weight = extract_single_weight(res_bom['weight'])

    material_json = {
        'mateCode': res_bom['code'],
        'mateName': res_bom['name'],
        'mateUnit': res_bom['mate_unit'],       # 物料单位
        'mateSource': res_bom['matesource'],    # 物料来源
        'unit': res_bom['unit'] or res_bom['mate_unit'],  # 物料转换单位
        'providerCode': res_bom['supplier_code'], # 供应商编码
        'providerName': res_bom['supplier_name'], # 供应商名称
        'price': str(res_bom['price']),              # 单价
        'element': res_bom['composition'],      # 成分
        "model": bom_size_value,                # 多规格，取第一个规格
        'weight': weight,                       # 克重
        'wastRate': 0,                          # 损耗率
        'part': res_bom['part'],                # 部位
        'mate5ource': 1,
        'remarks': res_bom['memo'],
        'colorList': colorList,                 # 物料配色
        'mateSizeList': matesizelist,           # 物料配码
        'mateColorPriceList': matecolorpricelist  # 物料单价
    }
    
    return material_json, res_bom['type_code']


if __name__ == "__main__":
    main()