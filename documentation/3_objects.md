# �������
dv�ļ��ɷ�Ϊ�ĸ���Σ����̡����졢���Ρ�������dvfileģ��Ϊ���Ƿֱ������࣬���ṩһЩ����������

�����ȴ���һ�µ�print˵��#�������������ӵģ�ԭ�����û�У�
```py
>>> print(d)
#���̶��� Dvfile
[(0, 174.0)] #���ٱ�� 
[(-3, 3, 4)] #���ı��
 track ����-���� #������� Dvtrack
  segment 5760 111360 ������ ����_CHN_Normal_Build006 #���ζ��� Dvsegment
   7200 480 58 Ҳ ye #�������� Dvnote
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
## ������������
tick����dv�ļ��е�ʱ�䵥λ��480tickΪһ���ķ���������midi��׼��ͬ��

## ���̶��� Dvfile
Dvfile��ʾһ��dv�ļ�����opendv��dv�ļ��󷵻صı���Dvfile����

ע��Dvfile��dvfile������ȫСд��dvfile��ģ����������ĸ��д��Dvfile��dv���̶���

Dvfile�����������ԣ�

- tempo�����ٱ���б�����ÿ�����ٱ����Ԫ�飬Ԫ���һ��Ϊ���ٱ������λ�ã�int����λtick�����ڶ���Ϊ�����ٱ�Ǻ�����٣�float��
- beats�����ı���б�����ÿ�����ı����Ԫ�飬Ԫ���һ��Ϊ���ı������С�ڣ��ڶ���Ϊ���ӣ�ÿС��������int����������Ϊ��ĸ��x������Ϊ1�ģ�int��ֻ��Ϊ1,2,4,8,16,32��
- track�������б�ÿһ����һ��Dvtrack����
- inst�����������б�ÿһ����һ��Dvinst����

Dvfile֧�����²�����

- �ļ�ת����
    
    ��һ������У�use_hanzi��������ļ���ʹ�ú��ֻ���ƴ����Ĭ��ΪFalse��ƴ��
    - save(filename:str)������Ϊdv�ļ�
    - to_midi_file(self,use_hanzi:bool)������mido.MidiFile������save�ɱ���Ϊmid�ļ�
    - to_ust_file(self,use_hanzi:bool)������utaufile.Ustfile������save�ɱ���Ϊust�ļ�
    - to_nn_file(self)������utaufile.Nnfile������save�ɱ���Ϊnn�ļ�
    - to_music21_score(self,use_hanzi:bool)������music21.stream.Score����

- ʱ���ỻ��
    
- �������ݲ���
    
    ��һ��������޸�Dvfile���������������������������Ϊ���ڽ�Լ�ڴ��ͬʱ��������Ĵ���д��������
    ```py
    d.transpose(2).quantize(60).to_music21_score(use_hanzi=True).show()��
    ```
    
    �������Ҫ�޸�ǰ�Ķ�������Ҫ�޸ĺ�Ķ�������ʹ��deepcopy���ƶ����ٽ��в�������Ҫʹ��copy��
    ```py
    import copy
    b=copy.deepcopy(a).transpose(2).quantize(60)
    ```

## ������� Dvtrack
Dvtrack��ʾһ��dv�ϳ����졣

Dvtrack�����������ԣ�
- name���������ƣ�str
- volume��������int��ȡֵ��Χ[0,100]
- balance����������ƽ�⣬int��ȡֵ��Χ[-50,50]
- mute��������bool
- solo�����࣬bool
- segment�������б�ÿһ����һ��Dvsegment����

Dvtrack֧�����²�����

## ���ζ��� Dvsegment
Dvsegment��ʾһ��dv����

Dvsegment�����������ԣ�
- start�����tick����-3С������int
- length������tick��int
- name����������str
- vbname����Դ����str
- note�������б�
- vol������Volume��ȡֵ��Χ[0,256]��numpy.array([[x,y]])
- pit������Pitch��������Ϊ��λ��ת����midi��׼��100����-1��ʾ��Ĭ��������numpy.array([[x,y]])
- bre������Breathness��ȡֵ��Χ[0,256]��numpy.array([[x,y]])
- gen�����ߣ��Ա�Gender��ȡֵ��Χ[0,256]��numpy.array([[x,y]])

## �������� Dvnote
Dvnote��ʾһ��dv����

Dvnote�����������ԣ�