import os
import inspect
import importlib.util
import importlib
import pkgutil

def get_classes_by_dirpath(package_path):
    """
    获取指定包路径下所有 .py 文件中的类。
    :param package_path: 包的绝对路径（例如：/path/to/pyscrapy/spiders）
    :return: 包含所有类的列表 [(类名, 类对象), ...]
    """
    classes = []

    # 遍历包目录下的所有文件
    for root, _, files in os.walk(package_path):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":  # 排除 __init__.py
                module_name = file[:-3]  # 去掉 .py 后缀
                module_path = os.path.join(root, file)

                # 动态导入模块
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # 获取模块中的所有类
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if obj.__module__ == module_name:  # 确保类属于当前模块
                        classes.append((name, obj))

    return classes

def get_classes_in_package(package_name):
    """
    获取指定包（如 pyscrapy.spiders）中所有模块的类。
    :param package_name: 包的模块路径（如 "pyscrapy.spiders"）
    :return: 包含所有类的列表 [(类名, 类对象), ...]
    """
    classes = []

    # 动态导入包
    package = importlib.import_module(package_name)

    # 遍历包中的所有子模块
    for _, module_name, _ in pkgutil.walk_packages(path=package.__path__, prefix=package_name + '.'):
        try:
            # 动态导入子模块
            module = importlib.import_module(module_name)

            # 获取模块中的所有类
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ == module_name:  # 确保类属于当前模块
                    classes.append((name, obj))
        except Exception as e:
            print(f"Failed to import module {module_name}: {e}")

    return classes

def get_attr_to_cls(attr_name: str, pkgpath: str) ->dict:
    cls_list = get_classes_in_package(pkgpath)
    clsdict = {}
    for cls_name, cls in cls_list:
        if hasattr(cls, attr_name):
            k = getattr(cls, attr_name)
            if k:
                clsdict[k] = cls
    return clsdict

def get_attr_val_by_spider_name(attr_name: str, spider_name: str):
    spidercls = get_attr_to_cls('name', 'pyscrapy.spiders').get(spider_name)
    return getattr(spidercls, attr_name)

# # 示例用法
# package_name = "pyscrapy.spiders"  # 替换为你的包路径
# all_classes = get_classes_in_package(package_name)

# # 示例用法
# package_path = "pyscrapy/spiders"  # 替换为你的包的绝对路径
# all_classes = get_classes_by_dirpath(package_path)

# # 打印所有类的名称
# for cls_name, cls in all_classes:
#     if hasattr(cls, 'name'):
#         print(f"Class: {cls_name}----name={cls.name}")
