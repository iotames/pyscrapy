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

- Microsoft Visual C++ 14.0 or greater is required

```
 raise distutils.errors.DistutilsPlatformError(
  distutils.errors.DistutilsPlatformError: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

- visual studio code 启动powershell命令报错

设置-更新和安全-开发者选项-PowerShell-允许本地PowerShell脚本在未签名的情况下运行

或

管理员运行 PowerShell, 输入 `set-executionpolicy remotesigned` , 再输入 `y` 确认

https://blog.csdn.net/Dontla/article/details/112692116
