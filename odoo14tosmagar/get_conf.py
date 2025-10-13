import configparser
import os


class Config:
    def __init__(self, config_file='config.conf'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self._load_config()
        
    def _load_config(self):
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"配置文件 {self.config_file} 不存在")
        
        # 读取配置文件
        self.config.read(self.config_file, encoding='utf-8')
        
        # 获取配置项
        # mes 配置
        self.baseURL = self.config.get('MES', 'baseURL')
        self.appkey = self.config.get('MES', 'appkey')
        self.appSecret = self.config.get('MES', 'appSecret')

        # postgresql 配置
        self.host = self.config.get('PostgreSQL', 'host')
        self.port = self.config.getint('PostgreSQL', 'port')
        self.database = self.config.get('PostgreSQL', 'database')
        self.username = self.config.get('PostgreSQL', 'username')
        self.password = self.config.get('PostgreSQL', 'password')
        
        # token配置
        self.token = self.config.get('Token', 'token')
    
    def get(self, section, key, default=None):
        """获取配置项"""
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def tokensave(self):
        """保存配置到文件"""
        try:
            # 检查是否存在'Token'部分，如果没有则添加
            if not self.config.has_section('Token'):
                self.config.add_section('Token')
            
            # 设置token值
            self.config.set('Token', 'token', self.token)
            
            # 写入配置文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
        except Exception as e:
            raise Exception(f"保存配置失败: {e}")