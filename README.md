## python 虚拟环境

```shell
# create virtual
python -m venv venv

# for linux
source venv/bin/activate
# for windows
.\venv\Scripts\activate.bat

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 依赖错误(Windows)

- 缺少头文件 `openssl/opensslv.h`

下载:  http://slproweb.com/download/Win64OpenSSL-3_0_1.exe

