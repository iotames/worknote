import os
import configparser


class Config:
    def __init__(self, config_file=None):
        # 获取当前脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 如果没有提供配置文件路径，使用同级目录下的config.conf
        if config_file is None:
            self.config_file = os.path.join(script_dir, 'config.conf')
        else:
            self.config_file = config_file
        
        self.config = configparser.ConfigParser()
        self._load_config()
        
    def _load_config(self):
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            # 检查是否有示例配置文件
            sample_file = f"{self.config_file}.sample"
            if os.path.exists(sample_file):
                raise FileNotFoundError(f"配置文件 {self.config_file} 不存在，请将 {sample_file} 复制并重命名为 {self.config_file}")
            else:
                raise FileNotFoundError(f"配置文件 {self.config_file} 不存在，且未找到示例配置文件")
        
        # 读取配置文件
        self.config.read(self.config_file, encoding='utf-8')
        
        # 获取配置项
        # mes 配置 - 从DEFAULT节读取
        self.baseURL = self.config.get('MES', 'baseurl')
        self.appkey = self.config.get('MES', 'appkey')
        self.appSecret = self.config.get('MES', 'appsecret')

        # postgresql 配置
        self.host = self.config.get('PostgreSQL', 'host')
        self.port = self.config.getint('PostgreSQL', 'port')
        self.database = self.config.get('PostgreSQL', 'database')
        self.username = self.config.get('PostgreSQL', 'username')
        self.password = self.config.get('PostgreSQL', 'password')
        
        # token配置
        if self.config.has_section('Token'):
            self.token = self.config.get('Token', 'token')
        else:
            self.token = None
    
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