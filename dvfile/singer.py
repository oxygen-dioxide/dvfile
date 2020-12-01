import struct
from typing import List,Tuple,Dict

def skreadint(file)->int:
    return struct.unpack("l",file.read(4))[0]

def skreadbytes(file)->bytes:
    return file.read(skreadint(file))

def skreadstr(file)->str:
    try:
        return str(skreadbytes(file),encoding="utf8")
    except UnicodeDecodeError:#����ַ���������unicode���룬�򷵻ؿ��ַ����������ᵼ�³���ֱ���˳�
        return ""

def skwritebool(n:bool)->bytes:
    return bytes([int(n)])

def skwriteint(n:int)->bytes:
    return struct.pack("l",n)

def skwritebytes(s:bytes)->bytes:
    return skwriteint(len(s))+s

def skwritestr(s:str)->bytes:
    return skwritebytes(bytes(s,"utf8"))

def skwritelist(l:list)->bytes:
    return skwritebytes(skwriteint(len(l))+b"".join([bytes(n) for n in l]))

#dv��Դ
class Dvbank():
    '''
    dv��Դ��
    path��·��
    singer������
    version������汾
    symbol�������б�[(����,����,Ԫ��)]
    vowel��Ԫ���б�[(Ԫ��,��Դ)]
    voicon���Ǹ����б�[str]
    unvcon���帨���б�[str]
    inde�����������б�[str]
    tail��β���б�[str]
    '''
    def __init__(self,
                path:str,
                singer:str,
                version:str,
                symbol:List[Tuple[str,str,str]]=[],
                vowel:List[Tuple[str,str]]=[],
                voicon:List[str]=[],
                unvcon:List[str]=[],
                inde:List[str]=[],
                tail:List[str]=[],
                pitch:str="",
                model:List[Tuple[str,str,int]]=[]):
        self.path:str=path
        self.singer:str=singer
        self.version:str=version
        self.symbol:List[Tuple[str,str,str]]=symbol
        self.vowel:List[Tuple[str,str]]=vowel
        self.voicon:List[str]=voicon
        self.unvcon:List[str]=unvcon
        self.inde:List[str]=inde
        self.tail:List[str]=tail
        self.pitch:str=pitch
        self.model=model
    
def openvb(path:str)->Dvbank:
    '''
    ��dv��Դ������Dvbank����
    Ŀǰ֧������汾6.1  6.0  5.1  4.02
    '''
    import os
    import json
    #��sksd
    sksdname="voice.sksd"
    for filename in os.listdir(path):
        if(filename.endswith(".sksd")):
            sksdname=os.path.join(path,filename)
            break
    with open(sksdname,encoding="utf-8-sig") as sksdfile:
        sksd=json.load(sksdfile)
    name=sksd["name"]
    version=sksd["version"]
    symbol=[]
    vowel=[]
    voicon=[]
    unvcon=[]
    inde=[]
    tail=[]
    pitch=""
    model=[]
    #��SKI
    with open(os.path.join(path,"SKI"),"rb") as skifile:
        headlength={"6.1":68,
                    "6.0":64,
                    "5.1":56,
                    "4.02":68}
        #�ļ�ͷ
        if(version in headlength):
            skifile.read(headlength[version])
            #6�����б�
            prons=skreadstr(skifile).split("|")
            if(version in {"6.0","6.1"}):
                symbol=[]
                for line in prons[0].split(";"):
                    symbol.append(tuple(line.split(",")))
                voicon=prons[1].split(",")
                unvcon=prons[2].split(",")
                vowel=[]
                for line in prons[3].split(";"):
                    vowel.append(tuple(line.split(",")))
                inde=prons[4].split(",")
                tail=prons[5].split(",")
            elif(version in ["5.1","4.02"]):
                symbol=[]
                for line in prons[0].split(";"):
                    symbol.append(tuple(line.split(",")))
                voicon=prons[1].split(",")
                vowel=[]
                for line in prons[2].split(";"):
                    vowel.append(tuple(line.split(",")))
                unvcon=list(set(i[1] for i in symbol)-set(voicon)-set(i[0] for i in vowel))
                tail=prons[3].split(",")
                inde=[]
            deleteemptystr(tail)
            deleteemptystr(inde)
            pitch=skreadstr(skifile)#�����Ǵ�������ף���Ŀǰ��ȷ��
            skifile.read(56)
            #dvģ���б�
            while(len(skifile.read(4))==4):
                skifile.read(4)#0
                mname=skreadstr(skifile)
                mpitch=skreadstr(skifile)
                mpointer=skreadint(skifile)
                skifile.read(4)#0
                model.append((mname,mpitch,mpointer))
    return Dvbank(os.path.abspath(path),
                name,
                version,
                symbol,
                vowel,
                voicon,
                unvcon,
                inde,
                tail,
                pitch,
                model)

