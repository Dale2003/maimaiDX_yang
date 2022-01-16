# maimaiDX

移植自 xybot 及 [mai-bot](https://github.com/Diving-Fish/mai-bot) 开源项目，基于HoshinoBot v2的街机音游 **舞萌DX** 的查询插件

项目地址：https://github.com/Yuri-YuzuChaN/maimaiDX

## 使用方法

1. 将该项目放在HoshinoBot插件目录 `modules` 下，或者clone本项目 `git clone https://github.com/Yuri-YuzuChaN/maimaiDX`
2. 下载静态资源文件，将该压缩文件解压至插件根目录，即 `maimaiDX/static` ，[下载链接](https://www.diving-fish.com/maibot/static.zip)
3. pip以下依赖：`pillow`, `retrying`
4. 在`config/__bot__.py`模块列表中添加 `maimaiDX`
5. 重启HoshinoBot

**插件默认为关闭状态，如发现BOT无反应，请手动开启插件**

## 指令

| 命令                                           | 功能                         |
| ---------------------------------------------- | ---------------------------- |
| 帮助maimaiDX                                   | 查看指令帮助                 |
| 今日舞萌                                       | 查看今天的舞萌运势           |
| XXXmaimaiXXX什么                               | 随机一首歌                   |
| 随个[dx/标准][绿黄红紫白]<难度>                | 随机一首指定条件的乐曲       |
| 查歌<乐曲标题的一部分>                         | 查询符合条件的乐曲           |
| [绿黄红紫白]id<歌曲编号>                       | 查询乐曲信息或谱面信息       |
| <歌曲别名>是什么歌                             | 查询乐曲别名对应的乐曲       |
| <id/歌曲别称>有什么别称                        | 查询歌曲别名                 |
| <id/歌曲别称> [添加/删除]别称 <歌曲别名>       | 添加或删除歌曲别名           |
| 定数查歌 <定数> 定数查歌 <定数下限> <定数上限> | 查询定数对应的乐曲           |
| 分数线 <难度+歌曲id> <分数线>                  | 展示歌曲的分数线             |
| 开启/关闭mai猜歌                               | 开关猜歌功能                 |
| b40 <游戏名>                                   | 查询b40                      |
| b50 <游戏名>                                   | 查询b50                      |
| 我要在<难度>上<分数>分 <游戏名>                | 查看推荐的上分乐曲           |
| 猜歌                                           | 顾名思义，识别id，歌名和别称 |
| 我要(在<难度>)上<分数>分 <名字>                | 查看推荐的上分乐曲           |
| <牌子名称>进度 <名字>                          | 查看牌子完成进度             |
| <等级><评价>进度 <名字>                        | 查看等级评价完成进度         |
| <等级> 分数列表 <名字>                          | 查看等级评价列表             |
| 查看排名,查看排行 <页数>/<名字>               | 查看水鱼网站的用户ra排行     |
| 添加机厅 <名称> <位置> <机台数量> <别称1> <别称2> ... |添加机厅信息            |
| 删除机厅 <名称>                                 | 删除机厅信息                 |
| 修改机厅 <名称> [数量/别称] [<数量>/添加/删除] <别称1> <别称2> ... |修改机厅信息|
| 订阅机厅 <名称>                                 | 订阅机厅，简化后续指令        |
| 查看订阅                                        | 查看群组订阅机厅的信息       |
| 取消订阅,取消订阅机厅                           | 取消群组机厅订阅             |
| 查找机厅,查询机厅,机厅查找,机厅查询 <关键词>     | 查询对应机厅信息            |
| <名称>人数设置,设定,增加,加,+,减少,减,-<人数>   | 操作排卡人数                 |
| <名称>有多少人,有几人,有几卡,几人,几卡          | 查看排卡人数                 |

## 更新说明

### 2022-01-16

1. 修复b40/b50查询@Ta人情况下无效的问题

### 2022-01-03

1. 修改获取音乐数据的函数，不在使用同步进程
2. 不再使用正则表达式获取@人员的QQ号
3. 不再使用CQ码方式发送图片
4. 修改大部分源码

### 2021-11-15

1. 在请求获取maimaiDX数据的函数添加 `@retry` 装饰器，遇到请求数据失败的情况时重新尝试请求

### 2021-10-18

1. 添加排卡功能，感谢 [CrazyKid](https://github.com/CrazyKidCN)

### 2021-10-14

1. 更新查看推荐的上分乐曲
2. 更新查看牌子完成进度
3. 更新查看等级评价完成进度
4. 查看水鱼网站的用户ra排行

### 2021-09-29

1. 更新b50、乐曲推荐功能，感谢 [BlueDeer233](https://github.com/BlueDeer233) 

### 2021-09-13 

1. 更新猜歌功能以及开关，感谢 [BlueDeer233](https://github.com/BlueDeer233) 


## 鸣谢

感谢 [CrazyKid](https://github.com/CrazyKidCN) 提供的源码支持

感谢 [Diving-Fish](https://github.com/Diving-Fish) 提供的源码支持

感谢 [BlueDeer233](https://github.com/BlueDeer233) 提供猜歌功能的源码支持

## License

MIT

您可以自由使用本项目的代码用于商业或非商业的用途，但必须附带 MIT 授权协议。
