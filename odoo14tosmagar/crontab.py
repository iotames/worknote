import os  # 添加缺失的os模块导入
import sys
import time
import logging
import subprocess
import traceback

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 保持DEBUG级别以显示详细信息
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    # handlers=[
    #     logging.FileHandler("odoo14tomagar.log"),
    #     logging.StreamHandler()
    # ]
)
logger = logging.getLogger("odoo14tomagar")

# 获取当前脚本所在目录
sCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 配置：要执行的脚本列表（按顺序）
SCRIPTS_TO_EXECUTE = [
    # 必须先执行的token脚本
    "magar_smanager_token.py",
    # 依赖token的其他脚本
    "magar_saveBaCustomer.py",
    "magar_saveBaProvider.py",
    "magar_batchSaveBaMate.py",
    "magar_saveBaItem.py",
    "magar_saveApsOrder.py",
    "magar_saveWmsPur.py",
]

def run_script(script_name):
    """执行指定的Python脚本"""
    logger.info(f"开始执行脚本: {script_name}")
    start_time = time.time()
    
    try:
        # 构建脚本的绝对路径
        script_path = os.path.join(sCRIPT_DIR, script_name)
        
        # 检查脚本是否存在
        if not os.path.exists(script_path):
            logger.error(f"脚本文件不存在: {script_path}")
            return False
        
        # 执行脚本 - 不捕获输出，让日志直接显示在控制台和文件中
        # 这样就能看到子脚本的实时日志输出了
        result = subprocess.run(
            [sys.executable, script_path],
            # 移除stdout=subprocess.PIPE和stderr=subprocess.PIPE
            # 让子脚本的输出直接输出到当前进程的标准输出和错误流
            cwd=sCRIPT_DIR  # 在脚本所在目录执行
        )
        
        # 计算执行时间
        execution_time = time.time() - start_time
        
        # 检查执行结果
        if result.returncode == 0:
            logger.info(f"脚本 {script_name} 执行成功 (耗时: {execution_time:.2f}秒)")
            return True
        else:
            logger.error(f"脚本 {script_name} 执行失败，返回码: {result.returncode} (耗时: {execution_time:.2f}秒)")
            return False
    
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"执行脚本 {script_name} 时发生异常: {str(e)} (耗时: {execution_time:.2f}秒)")
        logger.error(traceback.format_exc())
        return False


def task():
    """按顺序执行所有配置的脚本，确保先成功获取token"""
    logger.info("开始执行任务序列")
    
    # 1. 首先执行token脚本
    token_script = SCRIPTS_TO_EXECUTE[0]
    token_success = run_script(token_script)
    
    # 如果token获取成功，再执行其他脚本
    if token_success:
        logger.info("token获取成功，开始执行后续脚本")
        
        # 2. 执行其他依赖token的脚本
        all_success = True
        for script_name in SCRIPTS_TO_EXECUTE[1:]:
            script_success = run_script(script_name)
            logger.info(f"脚本 {script_name} 执行结果: {'成功' if script_success else '失败'}")
            if not script_success:
                all_success = False
        
        return all_success
    else:
        logger.error("token获取失败，中止后续脚本执行")
        return False


def main():
    """主函数，程序入口"""
    logger.info("===== 定时任务脚本启动 ====")
    logger.info(f"脚本目录: {sCRIPT_DIR}")
    logger.info(f"配置的待执行脚本: {', '.join(SCRIPTS_TO_EXECUTE)}")
    
    try:
        task()
    except Exception as e:
        logger.error(f"主程序执行异常: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        logger.info("===== 定时任务脚本结束 ====\n")


if __name__ == "__main__":
    main()