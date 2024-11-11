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
- `DB_TYPE`: 数据库类型，默认为 `sqlite`。

## 运行爬虫

```
scrapy crawl spidername -a arg1=abc -a arg2=cdf
```

## 其他爬虫命令

```
# 新建爬虫
scrapy genspider itcast "itcast.cn"
# 运行爬虫并导出数据
scrapy crawl books -o books.csv
```

> https://docs.scrapy.org/en/latest/intro/install.html#using-a-virtual-environment-recommended
> https://docs.scrapy.org/en/latest/topics/commands.html
> https://www.cnblogs.com/galengao/p/5780519.html