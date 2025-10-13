------------使用ods.s_manager更新部门用户关系表----------------------

INSERT INTO usercenter."departmentsUsers" (
    "departmentId", 
    "userId", 
    "isMain", 
    "isOwner",    -- 新增字段
    "createdAt", 
    "updatedAt"
)
SELECT 
    d.id AS "departmentId",
    u.id AS "userId",
    true AS "isMain",
    is_owner AS "isOwner",    -- 新增字段
    CURRENT_TIMESTAMP AS "createdAt",
    CURRENT_TIMESTAMP AS "updatedAt"
FROM (
    -- 获取ODS转换后的用户和部门ID
    SELECT
        s_manager_id + 10000 AS new_user_id,
        CASE 
            WHEN dd_depart_ids ~ '^[0-9]+$' 
            THEN CAST(dd_depart_ids AS INTEGER) + 10000
            ELSE NULL 
        END AS new_department_id,
        CASE WHEN ta.is_lead = 1 THEN true ELSE false END AS is_owner
    FROM ods.s_manager LEFT JOIN ods.erp_talent_archives ta ON ta.s_talent_archives_id = s_talent_id
    WHERE s_employee_num IS NOT NULL
        AND s_activate_flag = 1
        AND dd_depart_ids ~ '^[0-9]+$'  -- 仅处理有效部门ID
        AND s_account <> '骆大春(旧)'
) ods_data
JOIN usercenter.users u ON u.id = ods_data.new_user_id  -- 通过转换后的用户ID关联
JOIN usercenter.departments d ON d.id = ods_data.new_department_id  -- 通过转换后的部门ID关联
ON CONFLICT ("departmentId", "userId") 
DO UPDATE SET 
    "isMain" = EXCLUDED."isMain",
    "isOwner" = EXCLUDED."isOwner",  -- 新增字段
    "updatedAt" = EXCLUDED."updatedAt"
;
