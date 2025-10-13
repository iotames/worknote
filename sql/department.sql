----------只展示未被删除且上级部门也未被删除的部门------------
SELECT 
  curr.dd_id + 10000 AS new_id,  -- ID偏移量+10000
  curr.dd_name,
  -- 处理父ID：非空则偏移，空值转为0（表示根节点）
  CASE 
    WHEN curr.dd_parent_id IS NOT NULL THEN curr.dd_parent_id + 10000 
    ELSE 0 
  END AS new_parent_id,
  curr.s_en_name,
  curr.s_jp_name,
  COALESCE(curr.dd_created_time, CURRENT_TIMESTAMP) AS dd_created_time,
  COALESCE(curr.dd_updated_time, COALESCE(curr.dd_created_time, CURRENT_TIMESTAMP)) AS dd_updated_time,
  curr.dd_deleted_time,
  curr.sort,
  false as "isLeaf"
FROM ods.s_depart curr
LEFT JOIN ods.s_depart parent 
  ON curr.dd_parent_id = parent.dd_id  -- 连接上级部门
WHERE 
  curr.dd_deleted_time IS NULL          -- 当前部门未删除
  AND (
    curr.dd_parent_id IS NULL         -- 情况1: 顶级部门(无上级)
    OR 
    parent.dd_deleted_time IS NULL    -- 情况2: 有上级且上级未删除
  );

----------------展示所有未被删除的部门----------------------
SELECT
  dd_id,
  dd_name,
  s_en_name,
  s_jp_name,
  dd_parent_id,
  dd_created_time,
  dd_updated_time,
  dd_deleted_time,
  sort
FROM s_depart
WHERE dd_deleted_time IS NULL

-----------脏数据检查：找出上级部门的数据已被删除的部门--------------------
SELECT 
  child.dd_id,
  child.dd_name,
  child.s_en_name,
  child.s_jp_name,
  child.dd_parent_id,
  child.dd_created_time,
  child.dd_updated_time,
  child.dd_deleted_time,
  child.sort
FROM 
  s_depart child
LEFT JOIN 
  s_depart parent ON child.dd_parent_id = parent.dd_id
WHERE 
  child.dd_deleted_time IS NULL
  AND parent.dd_deleted_time IS NOT NULL;

------------更新上级部门ID和isLeaf-------------------------
UPDATE usercenter.departments A
SET "parentId" = B.id,
    "updatedAt" = CURRENT_TIMESTAMP
FROM usercenter.departments B
WHERE A."parentId" IS NULL 
  AND A."originParentId" IS NOT NULL 
  AND B."originId" = A."originParentId";

UPDATE usercenter.departments A
SET "isLeaf" = TRUE,
    "updatedAt" = CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM usercenter.departments C
    WHERE C."parentId" = A.id
);