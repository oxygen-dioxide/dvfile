# dvfile-python

![](https://gitee.com/oxygendioxide/dvfile/raw/master/resources/1.png)
（[《奋楫》](https://www.bilibili.com/video/BV1xJ411x754?from=search&seid=2690624188195353743)作曲：格里特/髅髅，作词：冥凰）

## 介绍

操作[deepvocal](https://www.deep-vocal.com/) dv文件的python库。

本python库依赖[numpy](https://numpy.org/)

由于dv文件为二进制文件，且没有官方文档或解析器，本项目无法保证与deepvocal完美兼容，如遇到文件解析错误欢迎在issue中提出。

## 安装

> pip install dvfile

## 功能

### dv文件

- 解析与保存dv文件
    
    目前可以解析的内容：

    - 曲速标记：位置、曲速
    - 节拍标记：位置、每小节拍数、音符分数
    - 音轨属性：音轨名、音轨音量、独奏、静音、双声道平衡
    - 区段属性：区段名、区段音源名、起点、长度
    - 音符属性：起点、长度、音高、歌词汉字、歌词拼音、滑音(弯曲深度、弯曲长度、头部滑音长度、尾部滑音长度)、颤音(颤音长度、颤音幅度、颤音速度、渲染出的颤音曲线)
    - 伴奏音轨：音轨名、音轨音量、独奏、静音、文件名、起点
    - 区段参数：音量、音调、气声、声线

    目前不能解析的内容（保存时将还原默认值）：

    - 音符属性：音素

- 导出ust、nn文件（需要[utaufile](https://gitee.com/oxygendioxide/utaufile)）
- 导出mid文件（需要[mido](https://mido.readthedocs.io/en/latest/index.html)）
- 导出五线谱（需要[music21](http://web.mit.edu/music21/doc/index.html)、[utaufile](https://gitee.com/oxygendioxide/utaufile)和[musescore](http://musescore.org)(独立软件)）
- 批量获取歌词
- 量化（将音符对齐到节拍线）
- 移调（音符与pit批量上下移动）

### dvtb文件
- 解析与保存dvtb文件

## 示例

```py
import dvfile as df

#打开dv文件
d=df.opendv("myproject.dv")

#导出mid文件(需要mido)
d.to_midi_file().save("myproject.mid")

#每个音轨单独导出ust文件
for (i,t) in enumerate(d.track):
    t.to_ust_file().save('myproject{}.ust'.format(i))

#每个音轨单独导出nn文件(需要utaufile)
for (i,t) in enumerate(d.track):
    t.to_nn_file().save('myproject{}.nn'.format(i))

#导出五线谱(需要music21和musescore)
d.to_music21_score().show()

#获取第0音轨第0区段的歌词（拼音与汉字）列表
tr=d.track[0]
seg=tr.segment[0]
pinyin=seg.getlyric()
hanzi=seg.getlyric(use_hanzi=True)

#将第0音轨的所有区段合并
tr.segment=[sum(tr.segment)]

#工程整体降低3key
d.transpose(-3)

#保存dv文件
d.save("myproject2.dv")

#打开dvtb文件
dt=df.opendvtb("myvoicebank.dvtb")
```

## 参与贡献

1.  Fork 本仓库
2.  新建 Feat_xxx 分支
3.  提交代码
4.  新建 Pull Request

## 相关链接

[deepvocal官网](https://www.deep-vocal.com/)

[sharpkey（deepvocal前身）视频教程](https://www.bilibili.com/video/BV1Us411r7u5)

[deepvocal toolbox 文档](https://share.weiyun.com/5snXMol)