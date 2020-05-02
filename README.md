# dvfile-python

#### 介绍

解析[Deepvocal](https://www.deep-vocal.com/) dv文件的python库。

由于dv文件为二进制文件，且没有官方文档或解析器，本项目无法保证与deepvocal完美兼容，如遇到文件解析错误欢迎在issue中提出。

#### 安装

> pip install dvfile

#### 功能

目前可以解析的内容：

- 曲速标记：位置、曲速
- 节拍标记：位置、每小节拍数、音符分数
- 音轨属性：音轨名、音轨音量
- 区段属性：区段名、区段音源名、起点、长度
- 音符属性：起点、长度、音高、歌词汉字、歌词拼音、滑音(弯曲深度、弯曲长度、头部滑音长度、尾部滑音长度)

目前不能解析的内容：

- 伴奏音轨
- 音轨属性：双声道平衡
- 区段参数：音量、音调、气声、声线
- 音符属性：音素、颤音

#### 示例

```py
import dvfile as df
#打开dv文件
d=df.opendv("myproject.dv")
#导出为mid文件
d.to_midi_file().save("myproject.mid")
#每个音轨单独导出为ust文件
for (i,t) in enumerate(d.track):
    t.to_ust_file().save('myproject{}.ust'.format(i))
```

#### 参与贡献

1.  Fork 本仓库
2.  新建 Feat_xxx 分支
3.  提交代码
4.  新建 Pull Request
