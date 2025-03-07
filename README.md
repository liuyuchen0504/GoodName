# GoodName

宝宝取名W 项目。使用 LLM 技术根据用户描述为用户取名字。

## 本地启动
> 环境要求：  
> Python == 3.11

首次启动服务需要初始化数据库环境
```bash
cd GoodName/service

python create_tables.py
```

1. 安装依赖
   ```bash
   # 进入项目目录 cd GoodName
   pip install -r requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
   ```
2. 启动服务
   - 本地启动
     ```bash
     python main.py
     ```
   - 服务器启动
     ```bash
     sh run.sh
     ```
