import re
from odoo_db_con import PostgreSQLConnector

# 从字符串中提取第一个出现的数字
def extract_single_weight(weight_str):
    if not weight_str:
        return None
    
    # 匹配第一个出现的数字
    pattern = r'(\d+\.?\d*)'
    match = re.search(pattern, str(weight_str))
    
    if match:
        return float(match.group(1))
    return None

# 获取产品BOM信息
def get_product_bom(db, res_id , res_name):
    # 2.1 查询款式BOM
    query_bom = """
                    select  b.design_no , 
                            c.name , c.code , c.composition , c.package_transform , c.price , c.weight , 
                            e.name as mate_unit , 
                            a.id as bom_id , d.code as type_code , a.quantity , a.unit_loss , a.memo , a.material_id ,
                            f.code as supplier_code,
                            f.name as supplier_name,
                            g.name as unit ,
                            i.name as part ,
                            case h.code when 'M1' then 1 when 'M2' then 3 when 'M3' then 2 when 'M4' then 2 else 1 end as matesource
                    from    public.ziyi_product_bom a inner join 
                            public.ziyi_product b on b.id = a.product_id inner join 
                            public.ziyi_base_material c on c.id = a.material_id inner join 
                            public.ziyi_base_material_type d on d.id = c.type_id left join 
                            public.ziyi_base_unit e on e.id = c.unit_id left join 
                            public.ziyi_base_partner f on f.id = c.supplier_id left join 
                            public.ziyi_base_unit g on g.id = c.min_package_unit_id left join 
                            public.ziyi_base_supplier_type h on h.id = a.supplier_type_id left join 
                            public.ziyi_base_parts i on i.id = a.parts_id
                    WHERE   a.active = true and b.active = true and 
                            b.id = %s and d.code in ('B','F')
                    order by d.id , a.sequence , a.id 
                    LIMIT 30
                """
    results_bom = db.execute_query(query_bom, [res_id]) 
    return results_bom