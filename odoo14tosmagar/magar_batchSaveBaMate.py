import requests
import json
import time
from get_conf import Config
from magar_smanager_token import MES_Get_token
from odoo_db_con import PostgreSQLConnector


# todo : 读取配置文件中的smanager_token , 如果不存在或者已过期, 则获取新的token
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
    print("\n开始查询物料资料: ")
    query = """
                SELECT  a.id as material_id, a.code, a.name, a.create_date , 
                        case when b.code = 'B' then '1' else '2' end as matetype , 
                        case when a.active then '1' else '0' end as state , 
                        c.name as unit ,
                        a.composition ,
                        d.code as categorycode,
                        d.name as categoryname , 
                        e.code as supplier_code,
                        e.name as supplier_name
                FROM    public.ziyi_base_material a inner join 
                        public.ziyi_base_material_type b on b.id = a.type_id inner join 
                        public.ziyi_base_unit c on c.id = a.unit_id inner join 
                        public.ziyi_base_mat_category_first d on d.id = a.first_id left join 
                        public.ziyi_base_partner e on e.id = a.supplier_id
                WHERE   --a.company_id = 2
                        --AND 
                        a.write_date > CURRENT_TIMESTAMP - INTERVAL '6 HOURS' LIMIT 500
    """
    results = db.execute_query(query)
    if not results:
        print("没有物料资料")
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

        json = {
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
        print(json)
        list_value.append(json)
        
    # 写入mes接口
    url = Config().baseURL + "/yzApi/batchSaveBaMate"
    headers = {
        "Content-Type": "application/json",
        "smagar-token": str_token
    }
    print(f"url: {url}")
    response = requests.post(url, headers=headers, json=list_value)
    print(response.json())


if __name__ == "__main__":
    main()