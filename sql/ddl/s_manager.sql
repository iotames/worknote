-- santic.s_manager definition

CREATE TABLE `s_manager` (
  `s_manager_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '后台管理员表',
  `s_creater` int(11) DEFAULT NULL COMMENT '用户创建者',
  `s_account` varchar(64) DEFAULT NULL COMMENT '账户',
  `s_account_pinyin` varchar(255) DEFAULT NULL COMMENT '姓名的拼音',
  `s_account_pinyin_first` varchar(255) DEFAULT NULL COMMENT '拼音首字母',
  `s_password` varchar(64) DEFAULT NULL COMMENT '密码',
  `s_cellphone` varchar(20) DEFAULT NULL COMMENT '手机号',
  `s_email` varchar(64) DEFAULT NULL COMMENT '电子邮箱',
  `s_activate_flag` int(1) DEFAULT NULL COMMENT '是否启用(1.启用 0禁用）',
  `s_unionid` varchar(255) DEFAULT NULL,
  `s_openid` varchar(255) DEFAULT NULL,
  `dd_depart_ids` text COMMENT '钉钉小程序部门表',
  `s_created_time` datetime DEFAULT NULL COMMENT '创建时间',
  `s_updated_time` datetime DEFAULT NULL,
  `s_deleted_time` datetime DEFAULT NULL,
  `s_lead_flag` tinyint(1) DEFAULT NULL COMMENT '最高领导者',
  `s_talent_id` int(11) DEFAULT NULL COMMENT '人事档案id',
  `s_mail_nickname` varchar(255) DEFAULT NULL COMMENT '邮箱昵称',
  `s_sys_language` varchar(10) DEFAULT 'zh' COMMENT '切换语言',
  `s_time_zone` int(11) DEFAULT NULL COMMENT '时区ID',
 
  PRIMARY KEY (`s_manager_id`) USING BTREE,
  UNIQUE KEY `s_manager_id` (`s_manager_id`) USING BTREE,
  KEY `s_activate_flag` (`s_activate_flag`) USING BTREE,
  KEY `s_account` (`s_account`) USING BTREE,
  KEY `s_cellphone` (`s_cellphone`)
) ENGINE=InnoDB AUTO_INCREMENT=5882 DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC COMMENT='后台管理员表';

----------------------------------------

DO $$
BEGIN
    -- 若ods模式不存在则创建
    IF NOT EXISTS (SELECT FROM information_schema.schemata WHERE schema_name = 'ods') THEN
        EXECUTE 'CREATE SCHEMA ods';
    END IF;
    -- 检查ods模式下的表是否存在
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'ods' AND table_name = 's_manager') THEN
        -- EXECUTE 'DROP TABLE ods.s_manager CASCADE';
        EXECUTE 'TRUNCATE TABLE ods.s_manager CASCADE'; 
    ELSE
        -- 创建表结构
        CREATE TABLE ods.s_manager (
            s_manager_id SERIAL PRIMARY KEY,
            s_creater INT,
            s_account VARCHAR(64),
            s_account_pinyin VARCHAR(255),
            s_account_pinyin_first VARCHAR(255),
            s_password VARCHAR(64),
            s_cellphone VARCHAR(20),
            s_email VARCHAR(64),
            s_activate_flag INT CHECK (s_activate_flag IN (0,1)),
            s_unionid VARCHAR(255),
            s_openid VARCHAR(255),
            dd_depart_ids TEXT,
            s_created_time TIMESTAMP,
            s_updated_time TIMESTAMP,
            s_deleted_time TIMESTAMP,
            s_lead_flag SMALLINT,
            s_talent_id INT,
            s_mail_nickname VARCHAR(255),
            s_sys_language VARCHAR(10) DEFAULT 'zh',
            s_time_zone INT
        );

        -- 添加注释
        COMMENT ON TABLE ods.s_manager IS '后台管理员表';
        COMMENT ON COLUMN ods.s_manager.s_creater IS '用户创建者';
        COMMENT ON COLUMN ods.s_manager.s_account IS '账户';
        COMMENT ON COLUMN ods.s_manager.s_account_pinyin IS '姓名的拼音';
        COMMENT ON COLUMN ods.s_manager.s_account_pinyin_first IS '拼音首字母';
        COMMENT ON COLUMN ods.s_manager.s_password IS '密码';
        COMMENT ON COLUMN ods.s_manager.s_cellphone IS '手机号';
        COMMENT ON COLUMN ods.s_manager.s_email IS '电子邮箱';
        COMMENT ON COLUMN ods.s_manager.s_activate_flag IS '是否启用(1.启用 0禁用）';
        COMMENT ON COLUMN ods.s_manager.s_unionid IS '微信开放平台unionid';
        COMMENT ON COLUMN ods.s_manager.s_openid IS '微信小程序openid';
        COMMENT ON COLUMN ods.s_manager.dd_depart_ids IS '钉钉部门ID列表';
        COMMENT ON COLUMN ods.s_manager.s_created_time IS '创建时间';
        COMMENT ON COLUMN ods.s_manager.s_updated_time IS '更新时间';
        COMMENT ON COLUMN ods.s_manager.s_deleted_time IS '逻辑删除时间';
        COMMENT ON COLUMN ods.s_manager.s_lead_flag IS '最高领导者标识';
        COMMENT ON COLUMN ods.s_manager.s_talent_id IS '人事档案ID';
        COMMENT ON COLUMN ods.s_manager.s_mail_nickname IS '邮箱显示昵称';
        COMMENT ON COLUMN ods.s_manager.s_sys_language IS '系统语言';
        COMMENT ON COLUMN ods.s_manager.s_time_zone IS '时区ID';
    END IF;
END 
$$;

--------------------------------------
SELECT
    s_manager_id,
    s_creater,
    s_account,
    s_account_pinyin,
    s_account_pinyin_first,
    s_password,
    s_cellphone,
    s_email,
    s_activate_flag,
    s_unionid,
    s_openid,
    dd_depart_ids,
    s_created_time,
    s_updated_time,
    s_deleted_time,
    s_lead_flag,
    s_talent_id,
    s_mail_nickname,
    s_sys_language,
    s_time_zone
FROM s_manager
WHERE s_activate_flag=1
AND s_account<>'骆大春(旧)'
