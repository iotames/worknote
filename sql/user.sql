------------用户------------------
SELECT
  s_manager_id + 10000 AS new_id,
  COALESCE(s_created_time, CURRENT_TIMESTAMP) AS s_created_time,
  COALESCE(s_updated_time, COALESCE(s_created_time, CURRENT_TIMESTAMP)) AS s_updated_time,
  s_deleted_time,
  s_account,
  s_talent_id,
  NULLIF(ta.s_email, '') AS s_email,
  ta.s_employee_num,
  ta.s_name,
  ta.s_depart,
  s_password,
  s_cellphone,
  s_activate_flag,
  s_unionid,
  s_openid,
  -- 修改点：对 dd_depart_ids 增加偏移量并重命名
  CASE 
    WHEN dd_depart_ids ~ '^[0-9]+$' 
    THEN CAST(dd_depart_ids AS INTEGER) + 10000  -- 数字类型偏移
    ELSE NULL 
  END AS new_department_id,  -- 重命名字段[9,10](@ref)
  s_lead_flag,
  s_time_zone
FROM ods.s_manager 
LEFT JOIN ods.erp_talent_archives ta 
  ON ta.s_talent_archives_id = s_talent_id
WHERE s_employee_num IS NOT NULL
  AND s_activate_flag = 1
  AND s_account <> '骆大春(旧)'
;

-------------查看有多少个工号重复的-------------------------
SELECT dd.s_employee_num, COUNT(dd.s_manager_id) as countid
FROM (
  SELECT ta.s_employee_num, m.s_manager_id, m.s_activate_flag
  FROM s_manager m
  LEFT JOIN erp_talent_archives ta ON ta.s_talent_archives_id = m.s_talent_id
  WHERE ta.s_employee_num IS NOT NULL
  AND m.s_account <> '骆大春(旧)'
) dd
WHERE dd.s_activate_flag = 1
GROUP BY dd.s_employee_num
HAVING COUNT(dd.s_manager_id) > 1;

------------电子邮箱重复------3---------------
SELECT s_email, COUNT(*) as count
FROM s_manager WHERE s_email IS NOT NULL AND s_activate_flag = 1 GROUP BY s_email HAVING COUNT(*) > 1;

------------手机号码重复---------2--------
SELECT s_cellphone, COUNT(*) as count
FROM s_manager WHERE s_cellphone IS NOT NULL AND s_activate_flag = 1 GROUP BY s_cellphone HAVING COUNT(*) > 1;

--------------账号名重复-----------11-----------
SELECT s_account, COUNT(*) as count
FROM s_manager WHERE s_account IS NOT NULL AND s_activate_flag = 1 GROUP BY s_account HAVING COUNT(*) > 1;

---------NocoBase v1.6.37-------------

CONSTRAINT users_email_key UNIQUE (email),
CONSTRAINT users_phone_key UNIQUE (phone),
CONSTRAINT users_username_key UNIQUE (username)