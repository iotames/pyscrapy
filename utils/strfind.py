import re

def get_material(desc) ->list:
    ml = []
    
    # 第一种模式：匹配 "数字% 字母" 格式
    pattern1 = re.compile(r'(\d+% [a-zA-Z]+)')
    matches1 = pattern1.findall(desc)
    if matches1:
        for i, match in enumerate(matches1):
            print(f"-----GetMaterial11[{i}]---m({match})----")
            ml.append(match)
    else:
        # 第二种模式：匹配 "字母 数字%" 格式
        pattern2 = re.compile(r'([a-zA-Z]+ \d+%)')
        matches2 = pattern2.findall(desc)
        if matches2:
            for i, match in enumerate(matches2):
                print(f"-----GetMaterial22[{i}]---m({match})----")
                ml.append(match)
    
    if not ml:
        # 第三种模式：匹配 "数字 % 字母" 格式
        pattern3 = re.compile(r'(\d+ % [a-zA-Z]+)')
        matches3 = pattern3.findall(desc)
        if matches3:
            for i, match in enumerate(matches3):
                print(f"-----GetMaterial333[{i}]---m({match})----")
                ml.append(match)
    
    return ml