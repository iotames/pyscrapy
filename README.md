## 安装依赖

### 全局安装

```
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 局部安装

```
# 创建虚拟环境
python -m venv venv

# 启动虚拟环境(windows)
venv\Scripts\activate.bat

# 启动虚拟环境(linux and mac)
source ./venv/bin/activate

# 在虚拟环境中安装依赖
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 配置

复制 `env.example` 文件为 `.env` 配置文件

- `HTTP_PROXY`: 爬虫代理，默认为空字符串。
- `DB_TYPE`: 数据库类型。仅支持 `postgresql` 和 `mysql`。


## 程序初始化

```
# 主要是初始化数据库
python main.py init
```

## 运行爬虫

```
scrapy crawl yourspidername

# 也可以添加自定义参数，在初始化爬虫实例时传入
scrapy crawl yourspidername -a arg1=abc -a arg2=cdf
```

## 其他爬虫命令

```
# 新建爬虫
scrapy genspider itcast "itcast.cn"
# 运行爬虫并导出数据
scrapy crawl itcast -o itcast.xlsx
```

> https://docs.scrapy.org/en/latest/intro/install.html#using-a-virtual-environment-recommended
> https://docs.scrapy.org/en/latest/topics/commands.html
> https://www.cnblogs.com/galengao/p/5780519.html