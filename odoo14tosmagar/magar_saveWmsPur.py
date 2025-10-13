import requests
import json
import time
from get_conf import Config
from magar_smanager_token import MES_Get_token
from odoo_db_con import PostgreSQLConnector

API_ENDPOINT = '/yzApi/saveWmsPur'
TIME_INTERVAL = '6 HOURS'
QUERY_LIMIT = 500


def main():
    
    try:
        # mes 配置
        config = Config()
        baseURL = config.baseURL
        str_token = config.token

        # postgresql 配置
        host = config.host
        port = config.port
        database = config.database
        username = config.username
        password = config.password
        
    except FileNotFoundError as e:
        print(f"错误: {e}")

    db = PostgreSQLConnector(host, port, database, username, password)
    print("\n开始查询采购合同: ")
    query = """
                SELECT  a.name , case when a.type = 'B' then 1 else 2 end as matetype, a.create_date, a.delivery_date as delivery_date, 
                        a.tax_rate , h.name as currency , a.currency_rate ,
                        b.code as supplier_code, b.name as supplier_name , d.contract_no , g.design_no as itemcode ,
                        i.login as creater
                FROM    public.ziyi_purchase_order a inner join 
                        public.ziyi_base_partner b on a.supplier_id = b.id inner join 
                        public.ziyi_purchase_order_line c on c.order_id = a.id inner join 
                        public.ziyi_sale_order d on d.id = c.order_id inner join 
                        public.ziyi_sale_order_line f on f.id = c.sale_order_line inner join 
                        public.ziyi_product g on g.id = f.product_id inner join 
                        public.res_currency h on h.id = a.currency_id left join 
                        public.res_users i on i.id = a.create_uid
                WHERE   a.active = true and
                        a.write_date > CURRENT_TIMESTAMP - INTERVAL '6 HOURS' 
                LIMIT 500;
                
    """
    # SELECT  a.name , case when a.type = 'B' then 1 else 2 end as matetype, a.create_date, a.delivery_date as delivery_date, 
    #         a.tax_rate , h.name as currency , a.currency_rate ,
    #         b.code as supplier_code, b.name as supplier_name , d.contract_no , g.design_no as itemcode ,
    #         i.login as creater
    # FROM    public.ziyi_purchase_order a inner join 
    #         public.ziyi_base_partner b on a.supplier_id = b.id inner join 
    #         public.ziyi_purchase_order_line c on c.order_id = a.id inner join 
    #         public.ziyi_sale_order d on d.id = c.order_id inner join 
    #         public.ziyi_sale_order_line f on f.id = c.sale_order_line inner join 
    #         public.ziyi_product g on g.id = f.product_id inner join 
    #         public.res_currency h on h.id = a.currency_id left join 
    #         public.res_users i on i.id = a.create_uid
    # WHERE   a.active = true and
    #         AND a.write_date > CURRENT_TIMESTAMP - INTERVAL '{TIME_INTERVAL}' 
    # --LIMIT {QUERY_LIMIT}
    results = db.execute_query(query)
    if not results:
        print("没有符合条件的采购合同")
        return

    for rec in results:
        orderbillno = f"{rec['contract_no']}_{rec['itemcode']}"
        json = {
                'billNo':   rec['name'],
                'mateType': rec['matetype'],
                'fillDate': rec['create_date'].strftime("%Y-%m-%d"),
                'providerCode': rec['supplier_code'],
                'providerName': rec['supplier_name'],
                'deliveryDate': rec['delivery_date'].strftime("%Y-%m-%d"),
                'orderBillNO' : orderbillno,  # 生产订单号
                'deliveryType': '' , # 	交货方式'??
                'taxRate': str(rec['tax_rate']), # 税率
                'currency': rec['currency'], # 币种
                'exchangeRate': str(rec['currency_rate']), # 汇率
                'creater': 	rec['creater'], # 创建人(admin)
                'checkTime' : rec['create_date'].strftime("%Y-%m-%d"), # 	审核日期 (yyyy-MM-dd HH:mm:ss)
                # # linkName	联系人
                # # linkTel	联系电话
                'state':1, # 状态 (状态：0:未审核；1:已审核；2，已作废；3，已结案)  默认为1

                # 'wmsPurListList': [{
                #         "mateCode": "ZF02000170",
                #         "mateName": "尼龙仿棉磨毛布",
                #         "po": "sssss",
                #         "qty": 10,
                #         "colorCode": "01",
                #         "colorName": "红色",
                #         "model": "140CM",
                #         "weight": 80,
                #         "price": 12,
                #         "customerCode": "0002",
                #         "customerName": "波司登集团",
                #     },
                #     {
                #     "mateCode": "ZF02000023",
                #     "mateName": "1867尼氨平纹200G防晒300+",
                #     "po": "aaaaa",
                #     "qty": 20,
                #     "colorCode": "02",
                #     "colorName": "白色",
                #     "model": "150CM",
                #     "weight": 90,
                #     "price": 18,
                #     "customerCode": "0002",
                #     "customerName": "波司登集团",
                # }]
                }
        
        # 写入mes接口
        url = baseURL + API_ENDPOINT
        headers = {
            "Content-Type": "application/json",
            "smagar-token": str_token
        }
        print(f"url: {url}")
        response = requests.post(url, headers=headers, json=json)
        print(response.json())


if __name__ == "__main__":
    main()