# �����ļ�����
��һ������Ŀ�ļ����µġ�zhiyaopingfan.dv����ֻҪƽ�����������Ƴ������ʣ����Ϊ��������dvfile�Ļ����ļ�������
## ���ļ�
���ȵ���dvfile��
```py
>>> import dvfile
```
��opendv���ļ�������һ��dv�ļ�����
```py
>>> d=dvfile.opendv("zhiyaopingfan.dv")
>>> type(d)
<class 'dvfile.Dvfile'>
```
������print��ӡ�����Ա���ٲ鿴��

ע�⣺dvfile���и��ֶ���print����������ں����汾��dvfile����ʱ���ܵ������Ż���Ӧ�����������н����������ԣ�����������ַ���������������ݡ�
```py
>>> print(d)
[(0, 174.0)]
[(-3, 3, 4)]
 track ����-����
  segment 5760 111360 ������ ����_CHN_Normal_Build006
   7200 480 58 Ҳ ye
   7680 480 59 �� xu
   8160 480 56 �� hen
   8640 480 58 Զ yuan
   9120 480 66 �� huo
   9600 480 65 �� shi
   10080 1440 65 �� zuo
   11520 1440 63 �� tian
   12960 960 61 �� zai
   13920 480 63 �� zhe
   14400 480 65 �� li
   14880 480 61 �� huo
   15360 480 56 �� zai
   15840 480 59 �� dui
   16320 960 58 �� an
......
```
## �����ļ�
dv�ļ����������save��������Ϊdv�ļ�
```py
>>> d.save("zhiyaopingfan2.dv")
```

## �ļ���ʽת��
dv�ļ�������Ե���ust��nn��mid�ļ�
```py
>>> d.to_ust_file().save("zhiyaopingfan.ust")#����ust����Ҫutaufile��
>>> d.to_nn_file().save("zhiyaopingfan.nn")#����nn����Ҫutaufile��
>>> d.to_midi_file().save("zhiyaopingfan.mid")#����mid����Ҫmido��
```
dvfile�ڵ����ļ�ʱ�����Ŀ���ļ���֧�ֺ���ƴ��˫�ظ�ʣ�ust��mid��music21������Ĭ��ʹ��ƴ������Ա�֤���������ļ����ԡ������Ҫ�������ָ�ʣ���ʹ��use_hanzi=True����
```py
d.to_midi_file(use_hanzi=True).save("zhiyaopingfan.mid")
```


## ����������
��װmusic1 musescore����������һ�µķ������úû����󣬿��Ե���������
```py
>>> d.to_music21_score(use_hanzi=True).show()
```
����music21��ܴ����д�����Ҫ�ȴ������ӣ�Ȼ����musescore���ڲ���ʾ�����ף����Ե���ΪͼƬ��pdf�ļ���
![](Resource/2020-08-11-19-58-16.png)