# ׼������

## python�İ�װ
��[python����](https://www.python.org/)����python��װ��

˫�����У���ѡ"Add Python 3.8 to PATH"�����"Install Now"

![](Resource/2020-08-11-09-15-09.png)

## dvfile��������İ�װ
��win+R������cmd���س�����������ʾ����������������

```
pip install dvfile
pip install utaufile
pip install mido
pip install music21
```
��music21��ϴ�����㲻��Ҫ���������ף����Բ�װ��

## musescore�İ�װ�뻷������
���Ҫ���������ף�����Ҫ��װmusescore

��[musescore����](https://www.musescore.org/)����musescore��װ����˫�����С�

��װ��ɺ���windows�����������롰musescore�����Ҽ������ļ�λ��

![](Resource/2020-08-11-09-30-23.png)

�Ҽ�����ļ����е�musescore��ݷ�ʽ�����ԣ����ơ�Ŀ�ꡱһ��

![](Resource/2020-08-11-09-36-52.png)

win+R������python���س�����python�����С������������ݣ�
```
from music21 import *
us = environment.UserSettings()
us['musescoreDirectPNGPath'] = r"<���musescoreλ��>"
us['musicxmlPath'] = r"<���musescoreλ��>"
```
����<���musescoreλ��>�滻Ϊ�ղŸ��ƵĿ�ݷ�ʽĿ��