-- santic.erp_talent_archives definition

CREATE TABLE `erp_talent_archives` (
  `s_talent_archives_id` int(11) NOT NULL AUTO_INCREMENT,
  `s_name` char(50) DEFAULT NULL COMMENT '姓名',
  `s_subcompany` char(255) DEFAULT NULL COMMENT '子公司 （没用，只是记录）',
  `s_subcompany_id` int(11) DEFAULT NULL COMMENT '子公司id',
  `s_depart` char(50) DEFAULT NULL COMMENT '部门（没用，只是记录）',
  `s_depart_id` bigint(11) DEFAULT NULL COMMENT '部门id',
  `s_talent_position` char(50) DEFAULT NULL COMMENT '职位（没用，只是记录）',
  `s_talent_position_id` int(11) DEFAULT NULL COMMENT '职位id',
  `s_gender` char(5) DEFAULT NULL COMMENT '性别',
  `s_entry_date` datetime DEFAULT NULL COMMENT '入职日期（可计算工龄（年），工龄（月））',
  `s_entry_comment` char(255) DEFAULT NULL COMMENT '入职批注',
  `s_entry_month` int(11) DEFAULT NULL COMMENT '入职月份',
  `s_probation` char(20) DEFAULT NULL COMMENT '试用期',
  `s_confirmation_date` datetime DEFAULT NULL COMMENT '转正日期',
  `s_political_outlook` char(20) DEFAULT NULL COMMENT '政治面貌（没用，只是记录）',
  `s_political_outlook_code` int(11) DEFAULT NULL COMMENT '政治面貌（1-，2-，3-）',
  `s_marriage` char(20) DEFAULT NULL COMMENT '婚否（没用，只是记录）',
  `s_marriage_code` int(11) DEFAULT NULL COMMENT '婚否（1-未婚 2-已婚 3-离异）',
  `s_education` char(50) DEFAULT NULL COMMENT '学历',
  `s_graduated_from` char(50) DEFAULT NULL COMMENT '毕业院校',
  `s_major` char(50) DEFAULT NULL COMMENT '专业',
  `s_bank_account` char(50) DEFAULT NULL COMMENT '银行账号',
  `s_opening_bank` char(50) DEFAULT NULL COMMENT '开户行（没用，只是记录）',
  `s_opening_bank_code` int(11) DEFAULT NULL COMMENT '开户行（1-，2-）',
  `s_census_register` char(255) DEFAULT NULL COMMENT '户籍',
  `s_ID_number` char(50) DEFAULT NULL COMMENT '身份证号码',
  `s_nation` char(20) DEFAULT NULL,
  `s_nation_code` int(11) DEFAULT NULL COMMENT '民族',
  `s_ID_card_validity` datetime DEFAULT NULL COMMENT '身份证有效期',
  `s_graduation_date` datetime DEFAULT NULL COMMENT '毕业时间',
  `s_current_address` char(255) DEFAULT NULL COMMENT '现住地址',
  `s_birth_date` datetime DEFAULT NULL COMMENT '出生日期',
  `s_birth_month` int(11) DEFAULT NULL COMMENT '生日月份',
  `s_contact_tel` char(50) DEFAULT NULL COMMENT '联系电话',
  `s_email` char(50) DEFAULT NULL COMMENT 'Email-邮箱',
  `s_home_contact` char(20) DEFAULT NULL COMMENT '家中联系人',
  `s_relationship` char(20) DEFAULT NULL COMMENT '关系',
  `s_contact_phone` char(50) DEFAULT NULL COMMENT '联系电话',
  `s_contract_expiration_time` datetime DEFAULT NULL COMMENT '合同到期时间',
  `s_contract_start_time` datetime DEFAULT NULL COMMENT '合同签订日期',
  `s_contract_signing_company` char(50) DEFAULT NULL COMMENT '合同签定公司',
  `s_medical_insurance` char(20) DEFAULT NULL COMMENT '医保',
  `s_social_security` varchar(20) DEFAULT NULL COMMENT '社保',
  `s_housing_subsidy` char(50) DEFAULT NULL COMMENT '安居补贴',
  `gmt_create` datetime DEFAULT NULL,
  `gmt_modified` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `is_delete` tinyint(2) DEFAULT '0',
  `s_change_type` int(11) DEFAULT NULL COMMENT '1-正式 2-试用 3-待入职 4-待离职 5-离职',
  `s_housing_subsidy_code` int(11) DEFAULT NULL COMMENT '安居补贴 1-已申请，2-未申请(弃用)',
  `s_probation_salary` decimal(10,2) DEFAULT NULL COMMENT '试用期薪资',
  `s_regular_salary` decimal(10,2) DEFAULT NULL COMMENT '固定薪资',
  `dd_avatar` varchar(255) DEFAULT NULL COMMENT '头像小图',
  `dd_big_avatar` varchar(255) DEFAULT NULL COMMENT '头像大图',
  `s_self_evaluation` text COMMENT '自我评价',
  `s_accumulation_fund` varchar(20) DEFAULT NULL COMMENT '公积金',
  `is_lead` int(11) DEFAULT NULL COMMENT '是否当前部门负责人 1 是',
  `s_lead_sort` int(5) DEFAULT NULL COMMENT '多个当前部门负责人排序情况',
  `advantage` text COMMENT '上级评价-优点',
  `disadvantage` text COMMENT '上级评价-待改进',
  `s_leave_time` datetime DEFAULT NULL COMMENT '离职时间',
  `s_leave_content` text COMMENT '离职原因',
  `s_system_division` int(2) DEFAULT NULL COMMENT '1 服装外贸业务\r\n2 跨境业务\r\n3 鞋类业务\r\n4 集团职能\r\n\r\n',
  `s_texture_source` int(1) DEFAULT NULL COMMENT '1、客样；2、材料部提供',
  `s_internal_referrer_name` varchar(255) DEFAULT NULL COMMENT '内部推荐人',
  `s_position_Level` varchar(255) DEFAULT NULL COMMENT '职级',
  `s_department_proxy_id` int(2) DEFAULT NULL COMMENT '部门代理人ID 1 第一代理人 2 第二代理人 NULL 否',
  `s_talent_category_id` varchar(2) DEFAULT NULL COMMENT '人才类型ID 1 关键人才 2 核心人才 3 否 多选',
  `s_employee_num` varchar(255) DEFAULT NULL COMMENT '工号',
  PRIMARY KEY (`s_talent_archives_id`),
  KEY `s_talent_archives_id` (`s_talent_archives_id`),
  KEY `s_name` (`s_name`),
  KEY `s_contact_tel` (`s_contact_tel`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='人才档案库';

---------------------------------
DO $$
BEGIN
    -- 若ods模式不存在则创建
    IF NOT EXISTS (SELECT FROM information_schema.schemata WHERE schema_name = 'ods') THEN
        EXECUTE 'CREATE SCHEMA ods';
    END IF;
    -- 检查ods模式下的表是否存在
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'ods' AND table_name = 'erp_talent_archives') THEN
        -- EXECUTE 'DROP TABLE ods.erp_talent_archives CASCADE';
        EXECUTE 'TRUNCATE TABLE ods.erp_talent_archives CASCADE'; 
    ELSE
        -- 创建表结构
        CREATE TABLE ods.erp_talent_archives (
            s_talent_archives_id SERIAL PRIMARY KEY,
            s_name VARCHAR(50),
            s_subcompany VARCHAR(255),
            s_subcompany_id INTEGER,
            s_depart VARCHAR(50),
            s_depart_id BIGINT,
            s_talent_position VARCHAR(50),
            s_talent_position_id INTEGER,
            s_gender VARCHAR(5),
            s_entry_date TIMESTAMP,
            s_entry_comment VARCHAR(255),
            s_entry_month INTEGER,
            s_probation VARCHAR(20),
            s_confirmation_date TIMESTAMP,
            s_political_outlook VARCHAR(20),
            s_political_outlook_code INTEGER,
            s_marriage VARCHAR(20),
            s_marriage_code INTEGER,
            s_education VARCHAR(50),
            s_graduated_from VARCHAR(50),
            s_major VARCHAR(50),
            s_bank_account VARCHAR(50),
            s_opening_bank VARCHAR(50),
            s_opening_bank_code INTEGER,
            s_census_register VARCHAR(255),
            s_ID_number VARCHAR(50),
            s_nation VARCHAR(20),
            s_nation_code INTEGER,
            s_ID_card_validity TIMESTAMP,
            s_graduation_date TIMESTAMP,
            s_current_address VARCHAR(255),
            s_birth_date TIMESTAMP,
            s_birth_month INTEGER,
            s_contact_tel VARCHAR(50),
            s_email VARCHAR(50),
            s_home_contact VARCHAR(20),
            s_relationship VARCHAR(20),
            s_contact_phone VARCHAR(50),
            s_contract_expiration_time TIMESTAMP,
            s_contract_start_time TIMESTAMP,
            s_contract_signing_company VARCHAR(50),
            s_medical_insurance VARCHAR(20),
            s_social_security VARCHAR(20),
            s_housing_subsidy VARCHAR(50),
            gmt_create TIMESTAMP,
            gmt_modified TIMESTAMP,
            is_delete BOOLEAN DEFAULT FALSE,
            s_change_type INTEGER,
            s_housing_subsidy_code INTEGER,
            s_probation_salary NUMERIC(10,2),
            s_regular_salary NUMERIC(10,2),
            dd_avatar VARCHAR(255),
            dd_big_avatar VARCHAR(255),
            s_self_evaluation TEXT,
            s_accumulation_fund VARCHAR(20),
            is_lead INTEGER,
            s_lead_sort INTEGER,
            advantage TEXT,
            disadvantage TEXT,
            s_leave_time TIMESTAMP,
            s_leave_content TEXT,
            s_system_division INTEGER,
            s_texture_source INTEGER,
            s_internal_referrer_name VARCHAR(255),
            s_position_Level VARCHAR(255),
            s_department_proxy_id INTEGER,
            s_talent_category_id VARCHAR(2),
            s_employee_num VARCHAR(255)
        );

        -- 创建索引
        CREATE INDEX ON ods.erp_talent_archives (s_name);
        CREATE INDEX ON ods.erp_talent_archives (s_contact_tel);

        -- 表注释
        COMMENT ON TABLE ods.erp_talent_archives IS '人才档案库';

        -- 列注释（关键字段示例）
        COMMENT ON COLUMN ods.erp_talent_archives.s_name IS '姓名';
        COMMENT ON COLUMN ods.erp_talent_archives.s_entry_date IS '入职日期（可计算工龄（年），工龄（月））';
        COMMENT ON COLUMN ods.erp_talent_archives.s_marriage_code IS '婚否（1-未婚 2-已婚 3-离异）';
        COMMENT ON COLUMN ods.erp_talent_archives.s_regular_salary IS '固定薪资';
        COMMENT ON COLUMN ods.erp_talent_archives.is_delete IS '删除标记（false：未删除，true：已删除）';
        COMMENT ON COLUMN ods.erp_talent_archives.s_system_division IS '1 服装外贸业务,2 跨境业务,3 鞋类业务,4 集团职能';
    END IF;
END 
$$;
-----------------------------------------

SELECT s_talent_archives_id
, s_name
, s_subcompany
, s_subcompany_id
, s_depart
, s_depart_id
, s_talent_position
, s_talent_position_id
, s_employee_num
, s_email
FROM erp_talent_archives
WHERE s_employee_num IS NOT NULL