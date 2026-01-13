"""测试OceanBase数据库连接"""

import os
import sys

import pymysql
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()


def test_connection():
    """测试数据库连接"""
    print("🔍 正在测试OceanBase连接...")
    print(f"Host: {os.getenv('DATABASE_HOST')}")
    print(f"Port: {os.getenv('DATABASE_PORT')}")
    print(f"User: {os.getenv('DATABASE_USER')}")
    print(f"Database: {os.getenv('DATABASE_NAME')}")
    print("-" * 50)

    try:
        conn = pymysql.connect(
            host=os.getenv("DATABASE_HOST"),
            port=int(os.getenv("DATABASE_PORT", 2881)),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD"),
            database=os.getenv("DATABASE_NAME", "test"),
            connect_timeout=10,
        )

        print("✅ 数据库连接成功！\n")

        # 获取版本信息
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"📌 OceanBase版本: {version[0]}\n")

        # 测试向量扩展
        try:
            cursor.execute("SHOW VARIABLES LIKE 'vector%'")
            vector_vars = cursor.fetchall()
            if vector_vars:
                print("✅ 向量扩展已启用")
                for var in vector_vars:
                    print(f"   {var[0]}: {var[1]}")
            else:
                print("⚠️  未检测到向量扩展变量（OceanBase 4.3+支持向量）")
        except Exception as e:
            print(f"ℹ️  向量扩展检查: {str(e)}")

        # 显示当前数据库
        cursor.execute("SELECT DATABASE()")
        current_db = cursor.fetchone()
        print(f"\n📂 当前数据库: {current_db[0]}")

        # 列出所有表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        if tables:
            print(f"\n📋 已有表格 ({len(tables)}):")
            for table in tables:
                print(f"   - {table[0]}")
        else:
            print("\n📋 数据库为空（尚未创建表）")

        conn.close()
        print("\n" + "=" * 50)
        print("✅ 所有测试通过！数据库已就绪。")
        print("=" * 50)
        return True

    except pymysql.err.OperationalError as e:
        print("\n❌ 连接失败（OperationalError）:")
        print(f"   错误码: {e.args[0]}")
        print(f"   错误信息: {e.args[1]}")
        print("\n💡 可能的原因:")
        print("   1. OceanBase服务未启动")
        print("   2. 连接信息不正确（host/port/user/password）")
        print("   3. 数据库不存在（首次使用需创建）")
        print("\n🔧 解决方案:")
        print("   - Docker本地部署:")
        print("     docker run -d --name oceanbase -p 2881:2881 \\")
        print("       -e MODE=mini oceanbase/oceanbase-ce")
        print("   - 或访问 https://cloud.oceanbase.com/ 注册云服务")
        return False

    except Exception as e:
        print(f"\n❌ 未知错误: {type(e).__name__}")
        print(f"   {str(e)}")
        return False


if __name__ == "__main__":
    # 检查.env文件是否存在
    if not os.path.exists(".env"):
        print("⚠️  未找到.env文件！")
        print("请先复制.env.example并填写配置:")
        print("   cp .env.example .env")
        print("   # 然后编辑.env文件填入实际凭证")
        sys.exit(1)

    success = test_connection()
    sys.exit(0 if success else 1)
