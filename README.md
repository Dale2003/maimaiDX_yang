# maimaiDX_yang

移植自Yuri-YuzuChaN的舞萌DX查分插件。

原作者项目地址：https://github.com/Yuri-YuzuChaN/maimaiDX



# 改动部分

## 写在前面

改动的一切功能均需要水鱼的开发者token，请联系水鱼获取。

static文件中加入了两个贴图，分别是yb50的小数点（dot.png）和羊的emoji贴图（yang.png），需要将这两个加在static文件夹中。

代码写得比较烂，绝大部分是往上堆重复的东西，因为有的地方不会改，反正现在这个bot被我改的面目全非，对不起原作者的代码（磕头

代码绝大部分新增功能为整活，图一乐即可。

## \_\_init\_\_.py 文件：

加入ap50、ap+50、yb50、worst50、random50、寸止50、锁血50、aaa50、sss50、ss50、x星b50、（等级）DX分数列表、（难度）（等级）分数列表、我有多菜。

## maimaidx_player_score.py 文件：

修改了分数列表部分，用类似b50的UI来绘制分数列表，并加入yang分。

加入“我有多菜”，获取rating排名。

在其中加入DX分数列表，也用类似b50的UI绘制。

## maimaidx_music_info.py 文件

修改minfo部分的UI，加入yang分。

## maimaidx_best_50.py 文件

修改部分UI，加入yang分。

## 新加入的文件

因为UI部分不太好改封装，所以我选择每个需要绘制UI的功能新开一个py文件。。。（捂脸

新加入的文件有：

maimaidx_yang_50.py

maimaidx_draw.py

maimaidx_draw_diff.py

maimaidx_star_b50.py

maimaidx_draw_dx.py

maimaidx_suoxie_50.py

maimaidx_cunzhi_50.py

maimaidx_aaa_50.py

maimaidx_ap_50.py

maimaidx_app_50.py

maimaidx_worst_50.py
