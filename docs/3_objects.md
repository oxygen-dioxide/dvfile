# 对象详解
dv文件可分为四个层次：工程、音轨、区段、音符。dvfile模块为它们分别建立了类，并提供一些函数操作。

我们先从上一章的print说起（#后的文字是我添加的，原输出中没有）
```py
>>> print(d)
#工程对象 Dvfile
[(0, 174.0)] #曲速标记 
[(-3, 3, 4)] #节拍标记
 track 歌声-音轨 #音轨对象 Dvtrack
  segment 5760 111360 新区段 飞梦_CHN_Normal_Build006 #区段对象 Dvsegment
   7200 480 58 也 ye #音符对象 Dvnote
   7680 480 59 许 xu
   8160 480 56 很 hen
   8640 480 58 远 yuan
   9120 480 66 或 huo
   9600 480 65 是 shi
   10080 1440 65 昨 zuo
   11520 1440 63 天 tian
   12960 960 61 在 zai
   13920 480 63 这 zhe
   14400 480 65 里 li
   14880 480 61 或 huo
   15360 480 56 在 zai
   15840 480 59 对 dui
   16320 960 58 岸 an
......
```
## 几个基本概念
tick：是dv文件中的时间单位，480tick为一个四分音符，与midi标准相同。

## 工程对象 Dvfile
Dvfile表示一个dv文件。用opendv打开dv文件后返回的便是Dvfile对象。

注意Dvfile与dvfile的区别：全小写的dvfile是模块名，首字母大写的Dvfile是dv工程对象。

Dvfile包含以下属性：

- tempo：曲速标记列表。其中每个曲速标记是元组，元组第一项为曲速标记所处位置（int，单位tick），第二项为该曲速标记后的曲速（float）
- beats：节拍标记列表。其中每个节拍标记是元组，元组第一项为节拍标记所处小节，第二项为分子（每小节拍数，int），第三项为分母（x分音符为1拍，int，只能为1,2,4,8,16,32）
- track：音轨列表，每一项是一个Dvtrack对象
- inst：伴奏音轨列表，每一项是一个Dvinst对象

Dvfile支持以下操作：

- 文件转换：
    
    这一类操作中，use_hanzi控制输出文件是使用汉字还是拼音。默认为False即拼音
    - save(filename:str)：保存为dv文件
    - to_midi_file(self,use_hanzi:bool)：导出mido.MidiFile对象，用save可保存为mid文件
    - to_ust_file(self,use_hanzi:bool)：导出utaufile.Ustfile对象，用save可保存为ust文件
    - to_nn_file(self)：导出utaufile.Nnfile对象，用save可保存为nn文件
    - to_music21_score(self,use_hanzi:bool)：导出music21.stream.Score对象

- 时间轴换算
    
- 自身内容操作
    
    这一类操作会修改Dvfile对象自身，并返回自身。这种设计是为了在节约内存的同时允许更简洁的代码写法。例如
    ```py
    d.transpose(2).quantize(60).to_music21_score(use_hanzi=True).show()。
    ```
    
    如果既需要修改前的对象，又需要修改后的对象，请先使用deepcopy复制对象再进行操作。不要使用copy。
    ```py
    import copy
    b=copy.deepcopy(a).transpose(2).quantize(60)
    ```

## 音轨对象 Dvtrack
Dvtrack表示一个dv合成音轨。

Dvtrack包含以下属性：
- name：音轨名称，str
- volume：音量，int，取值范围[0,100]
- balance：左右声道平衡，int，取值范围[-50,50]
- mute：静音，bool
- solo：独奏，bool
- segment：区段列表，每一项是一个Dvsegment对象

Dvtrack支持以下操作：

## 区段对象 Dvsegment
Dvsegment表示一个dv区段

Dvsegment包含以下属性：
- start：起点tick，从-3小节算起，int
- length：长度tick，int
- name：区段名，str
- vbname：音源名，str
- note：音符列表
- vol：音量Volume，取值范围[0,256]，numpy.array([[x,y]])
- pit：音调Pitch，以音分为单位，转换成midi标准的100倍，-1表示按默认音调，numpy.array([[x,y]])
- bre：气声Breathness，取值范围[0,256]，numpy.array([[x,y]])
- gen：声线（性别）Gender，取值范围[0,256]，numpy.array([[x,y]])

## 音符对象 Dvnote
Dvnote表示一个dv音符

Dvnote包含以下属性：