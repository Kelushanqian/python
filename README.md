创建虚拟环境
python -m venv .venv
激活虚拟环境
.venv\Scripts\activate
安装依赖，只用装一次
pip install -r requirements.txt
运行
python app.py

### 文件说明

processing.py
图片处理逻辑。
如果以后要调整处理算法，来这里改。

app.py
程序入口。连接前端。
运行方式：python app.py