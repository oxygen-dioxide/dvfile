__version__='0.1.0'

import copy
import numpy
from typing import List,Tuple

def skreadint(file)->int:
    return numpy.fromfile(file,"<i4",1)[0]

def skreadbytes(file)->bytes:
    return file.read(skreadint(file))

def skreadstr(file)->str:
    try:
        return str(skreadbytes(file),encoding="utf8")
    except UnicodeDecodeError:#如果字符串不能用unicode解码，则返回空字符串
        return ""

def skwritebool(n:bool)->bytes:
    return bytes([int(n)])

def skwriteint(n:int)->bytes:
    return numpy.array([n]).tobytes()

def skwritebytes(s:bytes)->bytes:
    return skwriteint(len(s))+s

def skwritestr(s:str)->bytes:
    return skwritebytes(bytes(s,"utf8"))

def skwritearray(ar)->bytes:
    return skwritebytes(skwriteint(ar.shape[0])+ar.tobytes())

def skwritelist(l:list)->bytes:
    return skwritebytes(skwriteint(len(l))+b"".join([bytes(n) for n in l]))

def intquantize(n:int,d:int)->int:
    return int(n/d+0.5)*d

def deleteemptystr(l:List[str]):
    #空字符串经过split后得到[""]，这里转为[]
    if(l!=[] and l[-1]==""):
        l.pop()

#dv文件
class Dvnote():
    '''
    dv音符类    
    start:起点，480为一拍，int
    length:长度，480为一拍，int
    notenum:音高，与midi相同，即C4为60，音高越高，数值越大，int
    hanzi:歌词汉字，str
    pinyin:歌词拼音，str
    benlen:弯曲长度，int
    bendep:弯曲深度，int
    porhead:头部滑音长度，int
    portail:尾部滑音长度，int
    timbre：采样音阶，-1表示跟随音高，0表示T1，1表示T2，以此类推，int
    viblen:颤音长度
    vibamp:颤音幅度曲线
    vibfre:颤音速度曲线
    vibp:渲染出的颤音音高曲线，单位：（毫秒，音分），上下颠倒，每10ms采样一次
    crolrc:交叉拼音，str
    crotim:交叉音阶，int
    '''
    def __init__(self,start:int,
                 length:int,
                 notenum:int,
                 pinyin:str,
                 hanzi:str,
                 benlen:int=0,
                 bendep:int=0,
                 porhead:int=0,
                 portail:int=20,
                 timbre:int=-1,
                 viblen:int=0,
                 vibamp=numpy.array([[-1,0],[100001,0]]),
                 vibfre=numpy.array([[-1,0],[100001,0]]),
                 vibp=numpy.array([[0,0]]),
                 crolrc:str="",
                 crotim:int=-1):
        self.start=start
        self.length=length
        self.notenum=notenum
        self.pinyin=pinyin
        self.hanzi=hanzi
        self.benlen=benlen
        self.bendep=bendep
        self.porhead=porhead
        self.portail=portail
        self.timbre=timbre
        self.viblen=viblen
        self.vibamp=vibamp
        self.vibfre=vibfre
        self.vibp=vibp
        self.crolrc=crolrc
        self.crotim=crotim
    
    def __str__(self):
        return "   {} {} {} {} {}\n".format(
            self.start,
            self.length,
            self.notenum,
            self.hanzi,
            self.pinyin)
    
    def __bytes__(self):
        from dvfile.data import data2
        v=self.vibp
        v[:,1]=-v[:,1]
        b=(skwriteint(self.start)
           +skwriteint(self.length)
           +skwriteint(115-self.notenum)
           +skwriteint(self.viblen)
           +skwritestr(self.pinyin)
           +skwritestr(self.hanzi)
           +b'\x00'
           +skwritebytes(skwritearray(self.vibamp)
                        +skwritearray(self.vibfre)
                        +skwritearray(v))
           +data2
           +b'\x00\x00\x00\x80?\x00\x00\x00\x80?\x00\x00\x80?\x00\x00\x80?'#音素
           +skwriteint(self.benlen)
           +skwriteint(self.bendep)
           +skwriteint(self.porhead)
           +skwriteint(self.portail)
           +skwriteint(self.timbre)
           +skwritestr(self.crolrc)
           +skwriteint(self.crotim))
        return b
    
class Dvsegment():
    '''
    dv区段类
    start:起点，480为一拍，从-3小节算起，int
    length:长度，480为一拍，int
    name:区段名，str
    vbname:音源名，str
    note:音符列表
    vol：音量Volume，取值范围[0,256]，numpy.array([[x,y]])
    pit：音调Pitch，以音分为单位，转换成midi标准的100倍，-1表示按默认音调，numpy.array([[x,y]])
    bre：气声Breathness，取值范围[0,256]，numpy.array([[x,y]])
    gen：声线（性别）Gender，取值范围[0,256]，numpy.array([[x,y]])
    '''
    def __init__(self,start:int,
                 length:int,
                 name:str="",
                 vbname:str="",
                 note:list=[],
                 vol=None,
                 pit=None,
                 bre=None,
                 gen=None):
        if(note==[]):
            note=[]
        self.start=start
        self.length=length
        self.name=name
        self.vbname=vbname
        self.note=note
        if(vol==None):
            self.vol=numpy.array([[-1,128],[length+1,128]])
        else:
            self.vol=vol
        if(pit==None):
            self.pit=numpy.array([[-1,-1],[length+1,-1]])
        else:
            self.pit=pit
        if(bre==None):
            self.bre=numpy.array([[-1,128],[length+1,128]])
        else:
            self.bre=bre
        if(gen==None):
            self.gen=numpy.array([[-1,128],[length+1,128]])
        else:
            self.gen=gen
        
    def __str__(self):
        s="  segment {} {} {} {}\n".format(
            self.start,
            self.length,
            self.name,
            self.vbname)
        for i in self.note:
            s+=str(i)
        return s
    
    def __bytes__(self):
        pit=self.pit
        sgn=(numpy.sign(pit[:,1])+1)//2
        pit[:,1]=(sgn-1)+sgn*(11550-pit[:,1])
        b=(skwriteint(self.start)
           +skwriteint(self.length)
           +skwritestr(self.name)
           +skwritestr(self.vbname)
           +skwritelist(self.note)
           +skwritearray(self.vol)
           +skwritearray(pit)
           +skwritearray(numpy.array([[-1,128],[self.length+1,128]]))
           +skwritearray(self.bre)
           +skwritearray(self.gen)
           +skwritearray(numpy.array([[-1,128],[self.length+1,128]]))
           +skwritearray(numpy.array([[-1,0],[self.length+1,128]]))
           )
        return b
    
    def __add__(self,other):
        #两个区段相加可合并区段
        #self为上一区段，other为下一区段
        deltatime=other.start-self.start#时间差
        seg=Dvsegment(start=self.start,
                      name=self.name,
                      vbname=self.vbname,
                      length=deltatime+other.length,
                      note=copy.deepcopy(self.note))
        notes=copy.deepcopy(other.note)
        for i in notes:
            i.start+=deltatime
        seg.note+=notes
        return seg

    def __radd__(self,other):
        #为适配sum，规定：其他类型+Dvsegment返回原Dvsegment
        return self
    
    def getlyric(self,use_hanzi:bool=False,ignore:set=set()):
        '''
        获取区段歌词列表
        默认使用dv文件中的拼音，如果需要使用汉字，use_hanzi=True
        ignore：忽略的歌词。例如如果想忽略连音符，则ignore={"-"}
        '''
        lyrics=[]
        if(use_hanzi):
            for n in self.note:
                if(not(n.hanzi in ignore)):
                    lyrics+=[n.hanzi]
        else:
            for n in self.note:
                if(not(n.pinyin in ignore)):
                    lyrics+=[n.pinyin]
        return lyrics
    
    def sort(self):
        '''
        音符按开始时间排序
        '''
        def sortkey(note):
            return note.start
        self.note=sorted(self.note,key=sortkey)
        return self
        
    def cut(self,head:bool=True,tail:bool=True):
        '''
        切去开始时间为负数的音符，以及结束时间大于区段长度的音符
        （这些音符在deepvocal编辑器中是无效音符）
        head:是否切去开始时间为负数的音符,bool
        tail:是否切去结束时间大于区段长度的音符,bool
        '''
        if(head):
            for i in range(0,len(self.note)):
                if(self.note[i].start>=0):
                    break
            self.note=self.note[i:]
        if(tail):
            for i in range(len(self.note)-1,-1,-1):
                if(self.note[i].start+self.note[i].length<=self.length):
                    break
            self.note=self.note[:i+1]
        return self
    
    def quantize(self,d:int):
        '''
        将dv区段按照给定的分度值（四分音符为480）量化。
        将所有音符的边界四舍五入到d的整数倍，过短的音符将被删除。
        例如，如果需要量化到八分音符，请使用seg.quantize(240)
        '''
        note_new=[]
        for n in self.note:
            start=intquantize(self.start+n.start,d)
            end=intquantize(self.start+n.start+n.length,d)
            if(end>start):
                n.start=start-self.start
                n.length=end-start
                note_new+=[n]
        self.note=note_new
        return self
    
    def filter(self,f):
        '''
        按函数过滤区段中的音符
        输入：函数f，它只接受一个Dvnote类型的输入，且输出为bool
        func将在所有音符上作用一遍，保留返回True的那些音符，其他音符将被删除
        '''
        self.note=filter(f,self.note)
        return self

    def filterout(self,s,use_hanzi:bool=False):
        '''
        按集合过滤区段中的音符
        输入：集合/列表/元组/字符串s，若音符歌词属于s，则删除该音符
        默认使用拼音，如需使用汉字，use_hanzi=True
        '''
        if(use_hanzi):
            self.note=[n for n in self.note if not(n.hanzi in s)]
        else:
            self.note=[n for n in self.note if not(n.pinyin in s)]
        return self

    def to_ust_file(self,use_hanzi:bool=False):
        '''
        将dv区段对象转换为ust文件对象
        默认使用dv文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        from utaufile import Ustfile,Ustnote
        ust=Ustfile()
        time=0
        for note in self.note:
            if(note.start!=time):
                ust.note+=[Ustnote(length=(note.start-time),lyric="R",notenum=60)]
            if(use_hanzi):
                lyric=note.hanzi
            else:
                lyric=note.pinyin
            ust.note+=[Ustnote(length=note.length,lyric=lyric,notenum=note.notenum)]
            time=note.length+note.start
        return ust
    
    def to_nn_file(self):
        '''
        将dv区段对象转换为nn文件对象
        nn文件只支持32分音符（分度值为60），过短的音符将被删除
        '''
        from utaufile import Nnfile,Nnnote
        nnnotes=[]
        for n in self.note:
            start=intquantize(n.start,60)//60
            length=intquantize(n.start+n.length,60)//60-start
            if(length>0):
                nnnotes.append(Nnnote(hanzi=n.hanzi,
                                    pinyin=n.pinyin,
                                    start=start,
                                    length=length,
                                    notenum=n.notenum))
        return Nnfile(note=nnnotes)

    def to_midi_track(self,use_hanzi:bool=False):
        '''
        将dv区段对象转换为mido.MidiTrack文件对象
        默认使用dv文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        import mido
        track=mido.MidiTrack()
        time=0
        for note in self.note:
            if(use_hanzi):
                track.append(mido.MetaMessage('lyrics',text=note.hanzi,time=(note.start-time)))
            else:
                track.append(mido.MetaMessage('lyrics',text=note.pinyin,time=(note.start-time)))
            track.append(mido.Message('note_on', note=note.notenum,velocity=64,time=0))
            track.append(mido.Message('note_off',note=note.notenum,velocity=64,time=note.length))
            time=note.start+note.length
        track.append(mido.MetaMessage('end_of_track'))
        return track
    
    def to_music21_stream(self,use_hanzi:bool=False):
        '''
        将dv区段对象转换为music21 stream，并自动判断调性
        默认使用dv文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        return self.to_ust_file(use_hanzi).to_music21_stream()
    
class Dvtrack():
    '''
    dv音轨类
    name:音轨名，str
    volume:音量，int
    mute:静音，bool
    solo:独奏，bool
    segment:区段列表
    '''
    def __init__(self,name:str="",
                 segment:list=[],
                 volume:int=30,
                 mute:bool=False,
                 solo:bool=False):
        if(segment==[]):
            segment=[]
        self.name=name
        self.volume=volume
        #self.balance=balance
        self.mute=mute
        self.solo=solo
        self.segment=segment
        
    def __str__(self):
        s=" track {}\n".format(self.name)
        for i in self.segment:
            s+=str(i)
        return s
    
    def __bytes__(self):
        b=(b"\x00\x00\x00\x00"#tracktype
           +skwritestr(self.name)
           +bytes([int(self.mute)])
           +bytes([int(self.solo)])
           +skwriteint(self.volume)
           +b"\x00\x00\x00\x00"#左右声道平衡
           +skwritelist(self.segment)
           )
        return b
    
    def quantize(self,d:int):
        '''
        将dv音轨按照给定的分度值（四分音符为480）量化。
        将所有音符的边界四舍五入到d的整数倍，过短的音符将被删除。
        例如，如果需要量化到八分音符，请使用tr.quantize(240)
        '''
        new_seg=[]
        for seg in self.segment:
            segstart=intquantize(seg.start,d)
            segend=intquantize(seg.start+seg.length,d)
            seg=Dvsegment(segstart,0,seg.name,seg.vbname,[])+seg
            seg.length=segend-segstart
            seg.quantize(d)
            new_seg+=[seg]
        self.segment=new_seg
        return self
    
    def cut(self,head:bool=True,tail:bool=True):
        '''
        对音轨中的每个区段，切去开始时间为负数的音符，以及结束时间大于区段长度的音符
        （这些音符在deepvocal编辑器中是无效音符）
        head:是否切去开始时间为负数的音符,bool
        tail:是否切去结束时间大于区段长度的音符,bool
        '''
        for seg in self.segment:
            seg.cut(head=head,tail=tail)
        return self
    
    def filter(self,f):
        '''
        按函数过滤音轨中的音符
        输入：函数f，它只接受一个Dvnote类型的输入，且输出为bool
        func将在所有音符上作用一遍，保留返回True的那些音符，其他音符将被删除
        '''
        for seg in self.segment:
            seg.filter(f)
        return self

    def filterout(self,s,use_hanzi:bool=False):
        '''
        按集合过滤音轨中的音符
        输入：集合/列表/元组/字符串s，若音符歌词属于s，则删除该音符
        默认使用拼音，如需使用汉字，use_hanzi=True
        '''
        for seg in self.segment:
            seg.filterout(s,use_hanzi)
        return self

    def setvbname(self,vbname:str):
        """
        为音轨中的所有区段统一设置音源名
        """
        for seg in self.segment:
            seg.vbname=vbname
        return self

    def to_ust_file(self,use_hanzi:bool=False):
        '''
        将dv音轨对象转换为ust文件对象
        默认使用dv文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        return sum(self.segment,Dvsegment(0,0)).to_ust_file(use_hanzi)
    
    def to_nn_file(self):
        '''
        将dv音轨对象转换为nn文件对象
        '''
        return sum(self.segment,Dvsegment(0,0)).to_nn_file()
        pass

    def to_midi_track(self,use_hanzi:bool=False):
        '''
        将dv音轨对象转换为mido.MidiTrack文件对象
        默认使用dv文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        s=sum(self.segment,Dvsegment(0,0))
        return s.to_midi_track(use_hanzi)

    def to_music21_stream(self,use_hanzi:bool=False):
        '''
        将dv区段对象转换为music21 stream，并自动判断调性
        默认使用dv文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        return self.to_ust_file(use_hanzi).to_music21_stream()
    
class Dvinst():
    '''
    dv伴奏音轨类
    start:开始时间
    length:长度
    filename:文件名
    name:伴奏音轨名
    volume:音量
    mute:静音
    solo:独奏
    '''
    def __init__(self,
                 start:int,
                 length:int,
                 filename:str="",
                 name:str="",
                 volume:int=30,
                 mute:bool=False,
                 solo:bool=False,
                 ):
        self.start=start
        self.length=length
        self.filename=filename
        self.name=name
        self.volume=volume
        #self.balance=balance
        self.mute=mute
        self.solo=solo

    def __bytes__(self):
        b=(b"\x01\x00\x00\x00"#tracktype
        +skwritestr(self.name)
        +skwritebool(self.mute)
        +skwritebool(self.solo)
        +skwriteint(self.volume)
        +b"\x00\x00\x00\x00"#左右声道平衡
        +skwritebytes(
            b"\x01\x00\x00\x00"
            +skwriteint(self.start)
            +skwriteint(self.length)
            +skwritestr(self.name)
            +skwritestr(self.filename)
            )
        )
        return b

class Dvfile():
    '''
    dv文件类
    tempo:曲速标记列表，
        曲速标记：(位置,曲速)
    beats:节拍标记列表
        节拍标记：(小节数位置,每小节拍数,x分音符为1拍(只能为1,2,4,8,16,32))
    track:音轨列表
    inst:伴奏音轨列表
    '''
    def __init__(self,
                 tempo:List[Tuple[int,float]]=[(0,120.0)],
                 beats:List[Tuple[int,int,int]]=[(-3,4,4)],
                 track:list=[],
                 inst:list=[]):
        if(track==[]):
            track=[]
        if(inst==[]):
            inst=[]
        self.tempo=tempo
        self.beats=beats
        self.track=track
        self.inst=inst
        
    def __str__(self):
        s="{}\n{}\n".format(self.tempo,self.beats)
        for i in self.track:
            s+=str(i)
        return s
    
    def __bytes__(self):
        btempo=[skwriteint(i[0])+skwriteint(int(i[1]*100)) for i in self.tempo]
        bbeats=[numpy.array(i) for i in self.beats]
        b=(b'ext1ext2ext3ext4ext5ext6ext7'
           +skwritelist(btempo)
           +skwritelist(bbeats)
           +skwritelist(self.track+self.inst)[4:]
           )
        b=b'SHARPKEY\x05\x00\x00\x00'+skwritebytes(b) 
        return b
    
    def save(self,filename:str):
        '''
        保存dv文件
        filename:文件名
        '''
        with open(filename,mode="wb") as file:
            file.write(bytes(self))
        
    def pos2tick(self,bar:int,beat:int=1,tick:int=0)->int:
        '''
        根据beats进行时间换算：
        输入：（小节，拍子，拍内位置）（dv gui上的SONG POS）
        输出：从-3小节开始，四分音符为480的时间
        '''
        beats=self.beats
        for i in range(0,len(beats)):
            if(beats[i][0]>bar):
                beats=beats[0:i]
                break
        beats+=[(bar,beats[-1][1],beats[-1][2])]
        t=0
        for i in range(0,len(beats)-1):
            t+=(beats[i+1][0]-beats[i][0])*beats[i][1]*1920//beats[i][2]
        t+=(beat-1)*1920//beats[i][2]+tick
        return t
    
    def tick2pos(self,tick:int)->Tuple[int,int,int]:
        '''
        根据beats进行时间换算：
        输入：从-3小节开始，四分音符为480的时间
        输出：元组（小节，拍子，拍内位置）（dv gui上的SONG POS）
        '''
        beats=self.beats
        t=0
        for i in range(0,len(beats)-1):
            tc=t+(beats[i+1][0]-beats[i][0])*beats[i][1]*1920//beats[i][2]
            if(tc<tick):
                t=tc
            else:
                beats=beats[0:i+1]
                break
        bar=beats[-1][0]+int((tick-t)//(beats[-1][1]*1920/beats[i][2]))
        beat=int((tick-t)%(beats[-1][1]*1920/beats[i][2]))//(1920//beats[i][2])+1
        tick=(tick-t)%(1920//beats[i][2])
        return (bar,beat,tick)
    
    def tick2time(self,tick:int)->float:
        '''
        根据tempo进行时间换算：
        输入：从-3小节开始，四分音符为480的时间
        输出：从-3小节开始，以秒为单位的时间
        '''
        tempos=self.tempo
        for i in range(0,len(tempos)):
            if(tempos[i][0]>tick):
                tempos=tempos[0:i]
                break
        tempos+=[(tick,tempos[-1][1])]
        t=0.0
        for i in range(0,len(tempos)-1):
            t+=(tempos[i+1][0]-tempos[i][0])/(8*tempos[i][1])
        return t
    
    def time2tick(self,time:float)->int:
        '''
        根据tempo进行时间换算：
        输入：从-3小节开始，以秒为单位的时间
        输出：从-3小节开始，四分音符为480的时间
        '''
        tempos=self.tempo
        t=0
        for i in range(0,len(tempos)-1):
            tc=t+(tempos[i+1][0]-tempos[i][0])/(8*tempos[i][1])
            if(tc<time):
                t=tc
            else:
                tempos=tempos[0:i+1]
                break
        tick=tempos[-1][0]+int((time-t)*8*tempos[-1][1])
        return tick
    
    def quantize(self,d:int):
        '''
        将dv工程按照给定的分度值（四分音符为480）量化。
        将所有音符的边界四舍五入到d的整数倍，过短的音符将被删除。
        例如，如果需要量化到八分音符，请使用seg.quantize(240)
        '''
        for tr in self.track:
            tr.quantize(d)
        return self
    
    def cut(self,head:bool=True,tail:bool=True):
        '''
        对工程中的每个区段，切去开始时间为负数的音符，以及结束时间大于区段长度的音符
        （这些音符在deepvocal编辑器中是无效音符）
        head:是否切去开始时间为负数的音符,bool
        tail:是否切去结束时间大于区段长度的音符,bool
        '''
        for tr in self.track:
            tr.cut(head=head,tail=tail)
        return self
    
    def filter(self,func):
        '''
        按函数过滤工程中的音符
        输入：函数func，它只接受一个Dvnote类型的输入，且输出为bool
        func将在所有音符上作用一遍，保留返回True的那些音符，其他音符将被删除
        '''
        for tr in self.track:
            tr.filter(func)
        return self

    def filterout(self,s,use_hanzi:bool=False):
        '''
        按集合过滤工程中的音符
        输入：集合/列表/元组/字符串s，若音符歌词属于s，则删除该音符
        默认使用拼音，如需使用汉字，use_hanzi=True
        '''
        for tr in self.track:
            tr.filterout(s,use_hanzi)
        return self

    def setvbname(self,vbname:str):
        '''
        为工程中的所有区段统一设置音源名
        '''
        for tr in self.track:
            tr.setvbname(vbname)
        return self

    def to_midi_file(self,filename:str="",use_hanzi:bool=False):
        '''
        将dv文件对象转换为mid文件与mido.MidiFile对象
        默认使用dv文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        import mido
        mid = mido.MidiFile()
        ctrltrack=mido.MidiTrack()
        ctrltrack.append(mido.MetaMessage('track_name',name='Control',time=0))
        tick=0
        for i in self.tempo:
            ctrltrack.append(mido.MetaMessage('set_tempo',tempo=mido.bpm2tempo(i[1]),time=i[0]-tick))
            tick=i[0]
        mid.tracks.append(ctrltrack)
        for i in self.track:
            mid.tracks.append(i.to_midi_track(use_hanzi))
        if(filename!=""):
            mid.save(filename)
        return mid
    
    def to_ust_file(self,use_hanzi:bool=False)->list:
        '''
        将dv文件按音轨转换为ust文件对象的列表
        默认使用dv文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        usts=[]
        tempo=self.tempo[0][1]
        for tr in self.track:
            ust=tr.to_ust_file(use_hanzi)
            ust.properties["Tempo"]=tempo
            usts+=[ust]
        return usts
    
    def to_nn_file(self):
        '''
        将dv文件按音轨转换为nn文件对象的列表
        '''
        nns=[]
        tempo=self.tempo[0][1]
        for tr in self.track:
            nn=tr.to_nn_file()
            nn.tempo=tempo
            nns.append(nn)
        return nns

    def to_music21_score(self,use_hanzi:bool=False):
        '''
        将dv文件按音轨转换为music21乐谱对象
        默认使用dv文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        import music21
        sc=music21.stream.Score()
        for tr in self.track:
            p=music21.stream.Part(tr.to_music21_stream(use_hanzi=use_hanzi))
            p.partName=tr.name
            sc.append(p)
        return sc
    
def opendv(filename:str):
    '''
    打开sk或dv文件，返回Dvfile对象
    '''
    with open(filename,"rb") as file:
        #文件头
        file.read(48)
        #读曲速标记
        tempo=[]
        for i in range(0,skreadint(file)):
            tempo+=[(skreadint(file),skreadint(file)/100)]
        file.read(4)
        #读节拍标记
        beats=[]
        for i in range(0,skreadint(file)):
            beats+=[tuple(numpy.fromfile(file,"<i4",3))]
        track=[]
        inst=[]
        for i in range(0,skreadint(file)):
            #读音轨
            tracktype=skreadint(file)#合成音轨0，伴奏1
            if(tracktype==0):
                trackname=skreadstr(file)
                mute=(file.read(1)==b'\x01')
                solo=(file.read(1)==b'\x01')
                volume=skreadint(file)
                file.read(4)#左右声道平衡
                file.read(4)#区段占用空间
                segment=[]
                for i in range(0,skreadint(file)):
                    #读区段
                    segstart=skreadint(file)
                    seglength=skreadint(file)
                    segname=skreadstr(file)
                    vbname=skreadstr(file)
                    file.read(4)#音符占用空间
                    note=[]
                    for i in range(0,skreadint(file)):
                        #读音符
                        start=skreadint(file)
                        length=skreadint(file)
                        notenum=115-skreadint(file)
                        viblen=skreadint(file)#颤音长度
                        pinyin=skreadstr(file)
                        hanzi=skreadstr(file)
                        file.read(1)
                        #以下是数据块1,包含颤音幅度线和颤音速度线
                        data1=numpy.fromfile(file,"<i4",skreadint(file)//4)#未知数据块1,包含滑音幅度线和频率线
                        vibamp=data1[2:2+data1[1]*2].reshape([-1,2])#颤音幅度线
                        data1=data1[2+data1[1]*2:]
                        vibfre=data1[2:2+data1[1]*2].reshape([-1,2])#颤音速度线
                        data1=data1[2+data1[1]*2:]
                        vibp=data1[2:2+data1[1]*2].reshape([-1,2])
                        vibp[:,1]=-vibp[:,1]#渲染出的颤音音高曲线
                        #以上是未知数据块1
                        data2=skreadbytes(file)#未知数据块2
                        file.read(18)#音素
                        benlen=skreadint(file)#弯曲长度
                        bendep=skreadint(file)#弯曲深度
                        porhead=skreadint(file)#头部滑音长度
                        portail=skreadint(file)#尾部滑音长度
                        timbre=skreadint(file)#音阶
                        crolrc=skreadstr(file)#交叉拼音
                        crotim=skreadint(file)#交叉音阶
                        note+=[Dvnote(start,
                                      length,
                                      notenum,
                                      pinyin,
                                      hanzi,
                                      benlen,
                                      bendep,
                                      porhead,
                                      portail,
                                      timbre,
                                      viblen,
                                      vibamp,
                                      vibfre,
                                      vibp,
                                      crolrc,
                                      crotim)]
                    #以下是区段参数
                    #音量Volume，取值范围[0,256]
                    vol=numpy.fromfile(file,"<i4",skreadint(file)//4)[1:].reshape([-1,2])
                    #return numpy.fromfile(file,"<i4",skreadint(file)//4)
                    #音调Pitch，以音分为单位，转换成midi标准的100倍，-1表示按默认音调
                    pit=numpy.fromfile(file,"<i4",skreadint(file)//4)[1:].reshape([-1,2])
                    sgn=(numpy.sign(pit[:,1])+1)//2
                    pit[:,1]=(sgn-1)+sgn*(11550-pit[:,1])
                    skreadbytes(file)
                    #气声Breathness，取值范围[0,256]
                    bre=numpy.fromfile(file,"<i4",skreadint(file)//4)[1:].reshape([-1,2])
                    #声线（性别）Gender，取值范围[0,256]
                    gen=numpy.fromfile(file,"<i4",skreadint(file)//4)[1:].reshape([-1,2])
                    skreadbytes(file)
                    skreadbytes(file)
                    segment+=[Dvsegment(segstart,
                                        seglength,
                                        segname,
                                        vbname,
                                        note,
                                        vol=vol,
                                        pit=pit,
                                        bre=bre,
                                        gen=gen)]
                track+=[Dvtrack(trackname,segment,volume,mute,solo)]
            else:
                trackname=skreadstr(file)
                mute=(file.read(1)==b'\x01')
                solo=(file.read(1)==b'\x01')
                volume=skreadint(file)
                file.read(4)#左右声道平衡
                file.read(4)#区段占用空间
                if(skreadint(file)>0):#如果为0，则为空伴奏音轨
                    segstart=skreadint(file)
                    seglength=skreadint(file)
                    skreadstr(file)
                    fname=skreadstr(file)
                    inst+=[Dvinst(segstart,seglength,fname,trackname,volume,mute,solo)]
    return Dvfile(tempo=tempo,beats=beats,track=track,inst=inst)

#dvtb文件
class Dvtbfile():
    '''
    dvtb文件类
    symbol：音节列表，[(音节,辅音,元音)]
    vowel：元音列表，[(元音,来源)]
    voicon：浊辅音列表，[str]
    unvcon：清辅音列表，[str]
    inde：独立发音列表，[str]
    tail：尾音列表，[str]
    wavpath：wav路径，[str]
    build_all_models：是否生成所有模型，bool
    build_which_models：指定生成哪些模型，str
    modelpath：模型路径，str
    outputpath：声库输出路径，str
    pitch：音高列表，[str]
    vbname：声库名称，str
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
                 vbname:str=""):
        self.symbol=symbol
        self.vowel=vowel
        self.voicon=voicon
        self.unvcon=unvcon
        self.inde=inde
        self.tail=tail
        self.wavpath=wavpath
        self.build_all_models=build_all_models
        self.build_which_models=build_which_models
        self.modelpath=modelpath
        self.outputpath=outputpath
        self.pitch=pitch
        self.vbname=vbname

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
            +skwritestr(self.vbname))
        return b
    
    def save(self,filename:str):
        '''
        保存dvtb文件
        filename:文件名
        '''
        with open(filename,mode="wb") as file:
            file.write(bytes(self))
    
def opendvtb(filename:str):
    '''
    打开dvtb文件，返回Dvtbfile对象
    '''
    with open(filename,"rb") as file:
        file.read(27)
        #读字典
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
        #读wav目录
        wavpath=[]
        for i in range(0,skreadint(file)):
            wavpath+=[skreadstr(file)]
        build_all_models=file.read(1)==b'\x01'
        build_which_models=skreadstr(file)
        modelpath=skreadstr(file)
        outputpath=skreadstr(file)
        pitch=skreadstr(file).split(",")
        vbname=skreadstr(file)
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
                    vbname)

#dv音源
class Dvbank():
    '''
    dv音源类
    path：路径
    vbname：名称
    version：引擎版本
    symbol：音节列表，[(音节,辅音,元音)]
    vowel：元音列表，[(元音,来源)]
    voicon：浊辅音列表，[str]
    unvcon：清辅音列表，[str]
    inde：独立发音列表，[str]
    tail：尾音列表，[str]
    '''
    def __init__(self,
                path:str,
                vbname:str,
                version:str,
                symbol:List[Tuple[str,str,str]]=[],
                vowel:List[Tuple[str,str]]=[],
                voicon:List[str]=[],
                unvcon:List[str]=[],
                inde:List[str]=[],
                tail:List[str]=[]):
        self.path=path
        self.vbname=vbname
        self.version=version
        self.symbol=symbol
        self.vowel=vowel
        self.voicon=voicon
        self.unvcon=unvcon
        self.inde=inde
        self.tail=tail
    
def openvb(path:str):
    '''
    打开dv音源，返回Dvbank对象
    目前支持引擎版本6.1  6.0  5.1  4.02
    '''
    import os
    import json
    #读sksd
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
    #读SKI
    with open(os.path.join(path,"SKI"),"rb") as skifile:
        headlength={"6.1":68,
                    "6.0":64,
                    "5.1":56,
                    "4.02":68}
        #文件头
        if(version in headlength):
            skifile.read(headlength[version])
            #6大发音列表
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
            skreadstr(skifile)#可能是打包的音阶，但目前不确定
            skifile.read(56)
    return Dvbank(os.path.abspath(path),
                name,
                version,
                symbol,
                vowel,
                voicon,
                unvcon,
                inde,
                tail)

def main():
    a=openvb(r"E:\Music-----------------\S\singers\yongqi_beta_v0.91")
    print(a.__dict__)
    pass

if(__name__=="__main__"):
    main()