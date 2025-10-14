import requests
import json
import time
import logging
import requests  # 添加缺失的import
from get_conf import Config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("magar_smanager_token")

class MES_Get_token:
    def __init__(self, base_url, app_key, app_secret):
        """初始化MES token获取客户端"""
        self.base_url = base_url
        self.app_key = app_key
        self.app_secret = app_secret
        self.token = None  # 存储获取到的token
        
    def get_token(self):
        """
        从MES系统获取访问token
        
        Returns:
            str: 成功时返回获取到的token，失败时返回None
        """
        token_url = f"{self.base_url}/getToken"
        logger.info(f"开始获取token，请求URL: {token_url}")
        
        payload = {
            "appKey": self.app_key,
            "appSecret": self.app_secret
        }
        
        try:
            response = requests.post(
                token_url,
                json=payload,
                verify=False,  # 注意：生产环境应考虑启用SSL验证
                timeout=30
            )
            
            response.raise_for_status()  # 检查HTTP错误
            
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"响应解析失败: {e}")
                logger.error(f"原始响应内容: {response.text}")
                return None
            
            logger.debug(f"API响应: {result}")
            
            if result.get("code") == 0:
                if "data" in result and "token" in result["data"]:
                    self.token = result["data"]["token"]
                    logger.info(f"Token获取成功")
                    return self.token
                else:
                    logger.error(f"Token获取失败: {result.get('data', 'data不存在或token字段缺失')}")
            else:
                logger.error(f"Token获取失败: {result.get('msg', '未知错误')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"获取token时发生网络错误: {e}")
            return None
        except Exception as e:
            logger.error(f"获取token时发生未知错误: {e}")
            return None


def main():
    """主函数，用于获取token并保存到配置文件"""
    config = None
    try:
        # 从配置文件读取配置信息
        config = Config()
        baseURL = config.baseURL
        appkey = config.appkey
        appSecret = config.appSecret
        
        logger.info(f"配置信息加载成功")
        logger.debug(f"baseURL: {baseURL}")
        logger.debug(f"appkey: {appkey}")
        # 注意：不要在日志中记录敏感信息如appSecret
        
    except FileNotFoundError as e:
        logger.error(f"配置文件错误: {e}")
        return None
    except Exception as e:
        logger.error(f"读取配置信息时发生错误: {e}")
        return None
    
    try:
        # 创建MES客户端并获取token
        mes_client = MES_Get_token(baseURL, appkey, appSecret)
        token = mes_client.get_token()
        
        if token:
            logger.info(f"Token获取成功，长度: {len(token)}字符")
        else:
            logger.error("Token获取失败，无法继续")
            return None
        
        # 将token值写入到配置文件
        if token and config:
            try:
                config.token = token
                config.tokensave()
                logger.info("Token已成功写入配置文件")
            except Exception as e:
                logger.error(f"写入配置文件时发生错误: {e}")
        
        return token
        
    except Exception as e:
        logger.error(f"处理过程中发生错误: {e}")
        return None


if __name__ == "__main__":
    main()