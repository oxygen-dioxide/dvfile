# ����dvfile
dvfile�ǲ���deepvocal dv�ļ���python��

## dvfile�����˼��
1. �걸��dvfile��Ŀ����֧�ֶ�ȡ��д��dv�ļ���һ�����ԡ�Ϊ������numpy����Ч�ʡ����������exe�ȷ�������һ��������
2. ������ͨ��dvfile�����������������ļ�������ת����dvfileĿǰ֧�������¿����ת��
    - mido
    - music21
    - utaufile��������utaupyȡ����
3. �û��Ѻá�dvfile��ҪΪpython����ʽ�������û��Ż�ʹ�����顣
    - dvfile�ṩ�����api����fix�޸���transpose�Ƶ���quantize�����ȡ�
    - dvfile�Ķ���������޸������ͬʱ�᷵������������һ������ɶ��������
    ```py
    #�����������Ƶ�2��������������32������������ʾ������
    d.transpose(2).quantize(60).to_music21_score(use_hanzi=True).show()
    ```
