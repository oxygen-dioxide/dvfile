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


#dvtb�ļ�
class Dvtbfile():
    '''
    dvtb�ļ���
    symbol�������б�[(����,����,Ԫ��)]
    vowel��Ԫ���б�[(Ԫ��,��Դ)]
    voicon���Ǹ����б�[str]
    unvcon���帨���б�[str]
    inde�����������б�[str]
    tail��β���б�[str]
    wavpath��wav·����[str]
    build_all_models���Ƿ���������ģ�ͣ�bool
    build_which_models��ָ��������Щģ�ͣ�str
    modelpath��ģ��·����str
    outputpath���������·����str
    pitch�������б�[str]
    singer���������ƣ�str
    '''
    def __init__(self,
                 symbol:List[Tuple[str,str,str]]=[],
                 vowel:List[Tuple[str,str]]=[],
                 voicon:List[str]=[],
                 unvcon:List[str]=[],
                 inde:List[str]=[],
                 tail:List[str]=[],
                 wavpath:List[str]=[],
                 build_all_models:bool=True,
                 build_which_models:str="",
                 modelpath:str="",
                 outputpath:str="",
                 pitch:List[str]=[],
                 singer:str=""):
        self.symbol:List[Tuple[str,str,str]]=symbol
        self.vowel:List[Tuple[str,str]]=vowel
        self.voicon:List[str]=voicon
        self.unvcon:List[str]=unvcon
        self.inde:List[str]=inde
        self.tail:List[str]=tail
        self.wavpath:List[str]=wavpath
        self.build_all_models:bool=build_all_models
        self.build_which_models:str=build_which_models
        self.modelpath:str=modelpath
        self.outputpath:str=outputpath
        self.pitch:List[str]=pitch
        self.singer:str=singer

    def __bytes__(self):
        b=(b'SHARPKEYTOOLBOX\x01\x00\x00\x00\x12\x13\x00\x00\x00\x00\x00\x00'
           +skwritestr("\r\n".join([",".join(line) for line in self.symbol]))
           +skwritestr("\r\n".join([",".join(line) for line in self.vowel]))
           +skwritestr("\r\n".join(self.voicon))
           +skwritestr("\r\n".join(self.unvcon))
           +skwritestr("\r\n".join(self.inde))
           +skwritestr("\r\n".join(self.tail))
           +skwriteint(len(self.wavpath)))
        for i in self.wavpath:
            b+=skwritestr(i)
        b+=(skwritebool(self.build_all_models)
            +skwritestr(self.build_which_models)
            +skwritestr(self.modelpath)
            +skwritestr(self.outputpath)
            +skwritestr(",".join(self.pitch))
            +skwritestr(self.singer))
        return b
    
    def save(self,filename:str):
        '''
        ����dvtb�ļ�
        filename:�ļ���
        '''
        with open(filename,mode="wb") as file:
            file.write(bytes(self))
    
def opendvtb(filename:str)->Dvtbfile:
    '''
    ��dvtb�ļ�������Dvtbfile����
    '''
    with open(filename,"rb") as file:
        file.read(27)
        #���ֵ�
        symbol=[]
        for line in skreadstr(file).split("\r\n"):
            line=line.split(",")
            if(len(line)==3):
                symbol.append(tuple(line))
        vowel=[]
        for line in skreadstr(file).split("\r\n"):
            line=line.split(",")
            if(len(line)==2):
                vowel.append(tuple(line))
        voicon=skreadstr(file).split("\r\n")
        unvcon=skreadstr(file).split("\r\n")
        inde=skreadstr(file).split("\r\n")
        tail=skreadstr(file).split("\r\n")
        #��wavĿ¼
        wavpath=[]
        for i in range(0,skreadint(file)):
            wavpath+=[skreadstr(file)]
        build_all_models=file.read(1)==b'\x01'
        build_which_models=skreadstr(file)
        modelpath=skreadstr(file)
        outputpath=skreadstr(file)
        pitch=skreadstr(file).split(",")
        singer=skreadstr(file)
    return Dvtbfile(symbol,
                    vowel,
                    voicon,
                    unvcon,
                    inde,
                    tail,
                    wavpath,
                    build_all_models,
                    build_which_models,
                    modelpath,
                    outputpath,
                    pitch,
                    singer)