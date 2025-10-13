CREATE TABLE `s_depart` (
  `dd_id` bigint(11) unsigned NOT NULL AUTO_INCREMENT,
  `dd_create_dept_group` varchar(20) DEFAULT NULL,
  `dd_name` varchar(255) DEFAULT NULL,
  `code` VARCHAR(32),
  `s_en_name` varchar(500) DEFAULT NULL COMMENT '英文名',
  `s_jp_name` varchar(255) DEFAULT NULL COMMENT '日文名',
  `dd_parent_id` bigint(11) DEFAULT NULL,
  `dd_next_manager_id` varchar(50) DEFAULT NULL COMMENT '部门经理id/上级用户id',
  `dd_created_time` datetime DEFAULT NULL,
  `dd_updated_time` datetime DEFAULT NULL,
  `dd_deleted_time` datetime DEFAULT NULL,
  `dd_select_status` char(255) DEFAULT NULL,
  `s_lark_depart_id` char(255) DEFAULT NULL COMMENT '飞书部门id',
  `s_lark_parent_department_id` char(255) DEFAULT NULL,
  `sort` int(11) DEFAULT '99999' COMMENT '排序',
  `s_dictionary_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`dd_id`) USING BTREE,
  UNIQUE KEY `dd_id` (`dd_id`) USING BTREE,
  KEY `dd_deleted_time` (`dd_deleted_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC;

--------------------------------------
DO $$ 
BEGIN
    -- 若ods模式不存在则创建
    IF NOT EXISTS (SELECT FROM information_schema.schemata WHERE schema_name = 'ods') THEN
        EXECUTE 'CREATE SCHEMA ods';
    END IF;
    -- 检查ods模式下的表是否存在
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'ods' AND table_name = 's_depart') THEN
        -- EXECUTE 'DROP TABLE ods.s_depart CASCADE';
        EXECUTE 'TRUNCATE TABLE ods.s_depart CASCADE'; 
    ELSE
        -- 在ods模式下创建表结构
        CREATE TABLE ods.s_depart (
            dd_id BIGSERIAL PRIMARY KEY,  -- 自增主键 [4](@ref)
            dd_create_dept_group VARCHAR(20),
            dd_name VARCHAR(255),
            code VARCHAR(32),
            s_en_name VARCHAR(500),
            s_jp_name VARCHAR(255),
            dd_parent_id BIGINT,
            dd_next_manager_id VARCHAR(50),
            dd_created_time TIMESTAMP,
            dd_updated_time TIMESTAMP,
            dd_deleted_time TIMESTAMP,
            dd_select_status CHAR(255),
            s_lark_depart_id CHAR(255),
            s_lark_parent_department_id CHAR(255),
            sort INT DEFAULT 99999,
            s_dictionary_id INT
        );

        -- 表注释
        COMMENT ON TABLE ods.s_depart IS '部门信息表';

        -- 列注释（保留MySQL的COMMENT语义）[10](@ref)
        COMMENT ON COLUMN ods.s_depart.s_en_name IS '英文名';
        COMMENT ON COLUMN ods.s_depart.s_jp_name IS '日文名';
        COMMENT ON COLUMN ods.s_depart.dd_name IS '部门名称';
        COMMENT ON COLUMN ods.s_depart.code IS '部门编码';
        COMMENT ON COLUMN ods.s_depart.dd_next_manager_id IS '部门经理id/上级用户id';
        COMMENT ON COLUMN ods.s_depart.s_lark_depart_id IS '飞书部门id';
        COMMENT ON COLUMN ods.s_depart.sort IS '排序';
    END IF;
END 
$$;
------------------
SELECT
*
FROM s_depart
WHERE dd_deleted_time IS NULL