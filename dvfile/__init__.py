__version__='0.2.0'


import copy
import math
import numpy
import struct
from typing import List,Tuple,Dict,Union

def skreadint(file)->int:
    return struct.unpack("l",file.read(4))[0]

def skreadbytes(file)->bytes:
    return file.read(skreadint(file))

def skreadstr(file)->str:
    try:
        return str(skreadbytes(file),encoding="utf8")
    except UnicodeDecodeError:#如果字符串不能用unicode解码，则返回空字符串，而不会导致程序直接退出
        return ""

def skwritebool(n:bool)->bytes:
    return bytes([int(n)])

def skwriteint(n:int)->bytes:
    return struct.pack("l",n)

def skwritebytes(s:bytes)->bytes:
    return skwriteint(len(s))+s

def skwritestr(s:str)->bytes:
    return skwritebytes(bytes(s,"utf8"))

def skwritearray(ar:numpy.ndarray)->bytes:
    return skwritebytes(skwriteint(ar.shape[0])+ar.tobytes())

def skwritelist(l:list)->bytes:
    return skwritebytes(skwriteint(len(l))+b"".join([bytes(n) for n in l]))

def intquantize(n:int,d:int)->int:
    #将n四舍五入到d的整数倍
    return int(n/d+0.5)*d

def deleteemptystr(l:List[str]):
    #空字符串经过split后得到[""]，这里转为[]
    if(l!=[] and l[-1]==""):
        l.pop()

def cutparam(ar:numpy.ndarray,length:int,default:int,head:bool=True,tail:bool=True)->numpy.ndarray:
    l,r=numpy.interp((0,length),ar[:,0],ar[:,1]).astype(numpy.int)
    if(head):
        ar=ar[ar[:,0]>0]
        ar=numpy.append([[-1,default],
                         [0,l]],ar,axis=0)
    if(tail):
        ar=ar[ar[:,0]<length]
        ar=numpy.append(ar,[[length,r],
                           [length+1,default]],axis=0)
    return ar

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
    vibamp:颤音幅度曲线，numpy.array([[x,y]])
    vibfre:颤音速度曲线，numpy.array([[x,y]])
    vibp:渲染出的颤音音高曲线，numpy.array([[x,y]])，单位：（毫秒，音分），每10ms采样一次
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
                 vibamp:numpy.array=numpy.array([[-1,0],[100001,0]]),
                 vibfre:numpy.array=numpy.array([[-1,0],[100001,0]]),
                 vibp:numpy.array=numpy.array([[0,0]]),
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
           +skwriteint(self.bendep)
           +skwriteint(self.benlen)
           +skwriteint(self.portail)
           +skwriteint(self.porhead)
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
    singer:音源名，str
    note:音符列表
    vol：音量Volume，取值范围[0,256]，numpy.array([[x,y]])
    pit：音调Pitch，以音分为单位，转换成midi标准的100倍，0表示按默认音调，numpy.array([[x,y]])
    bre：气声Breathness，取值范围[0,256]，numpy.array([[x,y]])
    gen：声线（性别）Gender，取值范围[0,256]，numpy.array([[x,y]])
    '''
    def __init__(self,start:int,
                 length:int,
                 name:str="",
                 singer:str="",
                 note:List[Dvnote]=[],
                 vol:numpy.array=None,
                 pit:numpy.array=None,
                 bre:numpy.array=None,
                 gen:numpy.array=None):
        if(note==[]):
            note=[]
        self.start:int=start
        self.length:int=length
        self.name:str=name
        self.singer:str=singer
        self.note:List[Dvnote]=note
        NoneType=type(None)
        if(type(vol)==NoneType):
            self.vol=numpy.array([[-1,128],[length+1,128]])
        else:
            self.vol=vol
        if(type(pit)==NoneType):
            self.pit=numpy.array([[-1,-1],[length+1,-1]])
        else:
            self.pit=pit
        if(type(bre)==NoneType):
            self.bre=numpy.array([[-1,128],[length+1,128]])
        else:
            self.bre=bre
        if(type(gen)==NoneType):
            self.gen=numpy.array([[-1,128],[length+1,128]])
        else:
            self.gen=gen
        
    def __str__(self):
        s="  segment {} {} {} {}\n".format(
            self.start,
            self.length,
            self.name,
            self.singer)
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
           +skwritestr(self.singer)
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
                      singer=self.singer,
                      length=deltatime+other.length,
                      note=copy.deepcopy(self.note))
        notes=copy.deepcopy(other.note)
        for i in notes:
            i.start+=deltatime
        seg.note+=notes
        return seg

    def __radd__(self,other):
        #为适配sum，规定：其他类型+Dvsegment返回原Dvsegment的副本
        return copy.deepcopy(self)
    
    def setstart(self,start:int):
        """
        修改音轨起点而不改变音符和参数的绝对位置
        """
        delta=start-self.start
        self.start=start
        #音符移动
        for note in self.note:
            note.start-=delta
        #参数移动
        for param in (self.pit,self.vol,self.bre,self.gen):
            param[:,0]-=delta
        return self

    def getlyric(self,use_hanzi:bool=False,ignore:set=set())->List[str]:
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
        self.note=sorted(self.note,key=lambda x:(x.start,x.notenum))
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
    
    def cutparam(self,head:bool=True,tail:bool=True):
        """
        切去区段两端的无效参数
        head:是否切去区段开头的无效参数,bool
        tail:是否切去区段结尾的无效参数,bool
        """
        self.vol=cutparam(ar=self.vol,length=self.length,default=128,head=head,tail=tail)
        self.pit=cutparam(ar=self.pit,length=self.length,default=0,head=head,tail=tail)
        self.bre=cutparam(ar=self.bre,length=self.length,default=128,head=head,tail=tail)
        self.gen=cutparam(ar=self.gen,length=self.length,default=128,head=head,tail=tail)
        return self
    
    def fixnoteoverlap(self):
        """
        修复音符重叠
        起点相同的音符，保留音高最高的
        起点不同的重叠音符，截取前一个音符的重叠部分
        """
        self.sort()#按开始时间排序
        newnotelist=[]
        for (i,note) in enumerate(self.note[:-1]):
            nextnote=self.note[i+1]
            if(note.start<nextnote.start):#如果音符开始时间相同，则不输出。
                if(note.start+note.length>nextnote.start):
                    note.length=nextnote.start-note.start
                newnotelist.append(note)
        newnotelist.append(self.note[-1])
        self.note=newnotelist
        return self

    def fix(self):
        """
        自动修复区段：
        - 删除区段两端的无效音符和无效参数
        - 音符按开始时间排序
        - 修复音符重叠
        """
        return self.cut().cutparam().fixnoteoverlap()
    
    def quantize(self,d:int):
        '''
        将dv区段按照给定的分度值d（四分音符为480）量化。
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
        self.note=list(filter(f,self.note))
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

    def transpose(self,n:int):
        """
        对dv区段移调
        n：移调半音数，向上为正，向下为负。
        """
        for note in self.note:
            note.notenum+=n
        sgn=(numpy.sign(self.pit[:,1])+1)//2
        self.pit[:,1]+=sgn*n*100
        return self

    def basicpitch(self,tempolist:List[Tuple[int,float]]):
        """
        计算音轨的基础音高曲线
        """
        #暂不支持变速曲
        tempo=tempolist[0][1]
        tps=8*tempo
        bp=numpy.zeros(self.length)
        #有音符部分的基本音高
        for n in self.note:
            bp[n.start:n.start+n.length]=100*n.notenum
        #开头、结尾
        bp[0:self.note[0].start]=100*self.note[0].notenum
        bp[self.note[-1].start:]=100*self.note[-1].notenum
        #滑音
        #dv滑音机制：
        #0~100，80为0.25s，最大不超过音符长度一半
        def por(deltax,y1,y2):
            ls=numpy.linspace(-math.pi/2,math.pi/2,num=deltax,endpoint=False)
            p=((y1+y2)/2+(y2-y1)/2*numpy.sin(ls))
            return p
        
        for i in range(len(self.note)-1):
            lastnote=self.note[i]
            nextnote=self.note[i+1]
            porstart=lastnote.start+lastnote.length-min((lastnote.length//2,int(0.025*lastnote.portail*tempo)))
            porend=nextnote.start+min((nextnote.length//2,int(0.025*nextnote.porhead*tempo)))
            bp[porstart:porend]=por(porend-porstart,lastnote.notenum*100,nextnote.notenum*100).astype(numpy.int)
        #弯音
        #dv弯音机制：
        #弯曲段长度受benlen控制，benlen<50时，长度为0.375s。benlen>50时，长度线性变化。benlen=100时，长度为0.6875s
        #前段为直线，从(0,0)到(x,-y)其中x=0.09375s，不超过音符长度一半，
        #y=bendep*0.03
        #后段为正弦曲线
        def ben(length,benlen,bendep):
            x1=min((length//2,int(0.09375*tps)))
            if(benlen<=50):
                x2=int(0.375*tps)
            else:
                x2=int((0.0625+benlen*0.006875)*tps)
            x2=min((length,x2))
            b=numpy.zeros(length)
            b[0:x1]=numpy.linspace(0,-1,num=x1,endpoint=False)
            b[x1:x2]=por(x2-x1,-1,0)
            b=b*3*bendep
            return b
        for n in self.note:
            bp[n.start:n.start+n.length]+=ben(n.length,n.benlen,n.bendep).astype(numpy.int)
        #颤音
        for n in self.note:
            vib=numpy.interp(numpy.linspace(0,n.length-1,num=n.length),n.vibp[:,0]/1000.0*tps,n.vibp[:,1],left=0,right=0)
            bp[n.start:n.start+n.length]+=vib.astype(numpy.int)
        return bp

    def pitch(self,tempolist:List[Tuple[int,float]]):
        """
        计算音轨的音高曲线（包括基础音高曲线和编辑过的曲线部分）
        """
        #暂不支持变速曲
        p=self.basicpitch(tempolist)#基础音高曲线
        dp=numpy.interp(numpy.linspace(0,self.length-1,num=self.length),self.pit[:,0],self.pit[:,1],left=0,right=0)#编辑过的曲线部分
        sgn=(numpy.sign(dp)+1)//2
        return sgn*dp+(1-sgn)*p

    def to_ust_file(self,use_hanzi:bool=False):
        '''
        将dv区段对象转换为ust文件对象
        默认使用dv文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        from utaufile import Ustfile,Ustnote
        ust=Ustfile()
        time=0
        for note in self.note:
            if(note.start!=time):#休止符
                ust.note.append(Ustnote(length=(note.start-time),lyric="R",notenum=60))
            if(use_hanzi):
                lyric=note.hanzi
            else:
                lyric=note.pinyin
            ust.note.append(Ustnote(length=note.length,lyric=lyric,notenum=note.notenum))
            time=note.length+note.start
        if(self.length!=time):#末尾休止符
            ust.note.append(Ustnote(length=self.length-time,lyric="R",notenum=60))
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
        将dv区段对象转换为mido.MidiTrack对象
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
    
    def to_iftp_track(self,use_hanzi:bool=False,beat:int=4):
        #iftpy暂停开发，请勿使用
        import iftpy
        iftpnotes=[]
        barlen=480*beat
        if(use_hanzi):
            for n in self.note:
                iftpnotes.append(iftpy.Iftpnote(start=n.start/barlen,
                                                end=(n.start+n.length)/barlen,
                                                notenum=n.notenum,
                                                lyric=n.hanzi))
        else:
            for n in self.note:
                iftpnotes.append(iftpy.Iftpnote(start=n.start/barlen,
                                                end=(n.start+n.length)/barlen,
                                                notenum=n.notenum,
                                                lyric=n.pinyin))
        return iftpy.Iftptrack(note=iftpnotes,beat=beat,name=self.name)

def music21_stream_to_dv_segment(st)->Dvsegment:
    """
    将music21音轨对象转为dv区段
    """
    import music21
    dvnote=[]
    for note in st.flat.getElementsByClass(music21.note.Note):
        if(note.lyric==None):#连音符在music21中没有歌词
            lyric="-"
        else:
            lyric=note.lyric
        dvnote.append(Dvnote(start=int(note.offset*480),
                             length=int(note.duration.quarterLength*480),
                             notenum=note.pitch.midi,
                             pinyin=lyric,
                             hanzi=lyric))
    return Dvsegment(start=7680,length=int(st.duration.quarterLength*480),note=dvnote)

def midi_track_to_dv_segment(mtr,ticks_per_beat:int=480)->Dvsegment:
    """
    将mido midi音轨对象转为dv区段
    ticks_per_beat:midi音轨中每拍的tick数，默认480
    """
    tick=0
    lyric=""
    note:Dict[int,Tuple[str,int]]={}#{音高:(歌词,开始时间)}
    dvnote=[]
    for signal in mtr:
        tick+=signal.time
        if(signal.type=="note_on"):
            #将新音符注册到键位-音符字典中
            note[signal.note]=(lyric,tick)
        elif(signal.type=="note_off"):
            #从键位-音符字典中找到音符，并弹出
            if(signal.note in note):
                n=note.pop(signal.note)
                dvnote.append(Dvnote(start=int(n[1]*480/ticks_per_beat),
                            length=int((tick-n[1])*480/ticks_per_beat),
                            notenum=signal.note,
                            pinyin=n[0],
                            hanzi=n[0]))
        elif(signal.type=="lyrics"):
            lyric=signal.text
    return Dvsegment(start=7680,length=int(tick*480/ticks_per_beat),note=dvnote,name=mtr.name)

def to_dv_segment(a,track:int=0)->Dvsegment:
    """
    将其他类型的音轨工程对象a转为dv区段
    track：如果a为多轨对象，则转换第track轨，默认为0，int。
    支持对象类型：
    utaufile.Ustfile, utaufile.Nnfile, dvfile.Dvsegment, dvfile.Dvtrack, dvfile.Dvfile, mido.MidiTrack,
    mido.MidiFile, music21.stream.Stream, music21.stream.Measure, music21.stream.Part, music21.stream.Score
    """
    type_name=type(a).__name__
    #从对象类型到所调用函数的字典
    type_function_dict={
        "Dvsegment":copy.deepcopy,#dv区段对象
        "Dvtrack":lambda x:sum(x.segment),#dv音轨对象
        "Dvfile":lambda x:sum(x.track[track].segment),#dv工程对象
        "MidiTrack":midi_track_to_dv_segment,#mido音轨对象
        "MidiFile":lambda x:midi_track_to_dv_segment(x.tracks[track]),#mido文件对象
        "Stream":music21_stream_to_dv_segment,#Music21普通序列对象
        "Measure":music21_stream_to_dv_segment,#Music21小节对象
        "Part":music21_stream_to_dv_segment,#Music21多轨中的单轨对象
        "Score":lambda x:music21_stream_to_dv_segment(x.parts[track]),#Music21多轨工程对象
    }
    #如果在这个字典中没有找到函数，则默认调用a.to_dv_segment()
    return type_function_dict.get(type_name,lambda x:x.to_dv_segment())(a)

class Dvtrack():
    '''
    dv音轨类
    name:音轨名，str
    segment:区段列表
    volume:音量，int,[0,100]
    balance:左右声道平衡，int,[-50,50]
    mute:静音，bool
    solo:独奏，bool
    '''
    def __init__(self,name:str="",
                 segment:List[Dvsegment]=[],
                 volume:int=30,
                 balance:int=0,
                 mute:bool=False,
                 solo:bool=False):
        if(segment==[]):
            segment=[]
        self.name:str=name
        self.volume:int=volume
        self.balance:int=balance
        self.mute:bool=mute
        self.solo:bool=solo
        self.segment:List[Dvsegment]=segment
        
    def __str__(self):
        s=" track {}\n".format(self.name)
        for i in self.segment:
            s+=str(i)
        return s
    
    def __bytes__(self):
        from dvfile.data import balancewrite
        b=(b"\x00\x00\x00\x00"#tracktype
           +skwritestr(self.name)
           +bytes([int(self.mute)])
           +bytes([int(self.solo)])
           +skwriteint(self.volume)
           +balancewrite.get(self.balance,b"\0\0\0\0")
           +skwritelist(self.segment)
           )
        return b
    
    def quantize(self,d:int):
        '''
        将dv音轨按照给定的分度值d（四分音符为480）量化。
        将所有音符的边界四舍五入到d的整数倍，过短的音符将被删除。
        例如，如果需要量化到八分音符，请使用tr.quantize(240)
        '''
        new_seg=[]
        for seg in self.segment:
            segstart=intquantize(seg.start,d)
            segend=intquantize(seg.start+seg.length,d)
            seg=Dvsegment(segstart,0,seg.name,seg.singer,[])+seg
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
    
    def cutparam(self,head:bool=True,tail:bool=True):
        """
        切去区段两端的无效参数
        head:是否切去区段开头的无效参数,bool
        tail:是否切去区段结尾的无效参数,bool
        """
        for seg in self.segment:
            seg.cutparam(head,tail)
        return self

    def fixnoteoverlap(self):
        """
        修复音符重叠
        起点相同的音符，保留音高最高的
        起点不同的重叠音符，截取前一个音符的重叠部分
        """
        for seg in self.segment:
            seg.fixnoteoverlap()
        return self

    def fix(self):
        """
        自动修复音轨：
        - 删除区段两端的无效音符和无效参数
        - 音符按开始时间排序
        - 修复音符重叠
        """
        for seg in self.segment:
            seg.fix()

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

    def setsinger(self,singer:str):
        """
        为音轨中的所有区段统一设置音源名
        """
        for seg in self.segment:
            seg.singer=singer
        return self

    def transpose(self,n:int):
        """
        对dv音轨移调
        n：移调半音数，向上为正，向下为负。
        """
        for seg in self.segment:
            seg.transpose(n)
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
    
    def to_iftp_track(self,use_hanzi:bool=False,beat:int=4):
        #iftpy暂停开发，请勿使用
        seg=sum(self.segment,Dvsegment(0,0))
        seg.name=self.name
        return seg.to_iftp_track(use_hanzi=use_hanzi,beat=beat)

def to_dv_track(a,track:int=0)->Dvtrack:
    """
    将其他类型的音轨工程对象a转为dv音轨
    track：如果a为多轨对象，则转换第track轨，int。
    支持对象类型：
    utaufile.Ustfile, utaufile.Nnfile, dvfile.Dvsegment, dvfile.Dvtrack, dvfile.Dvfile, mido.MidiTrack,
    mido.MidiFile, music21.stream.Stream, music21.stream.Measure, music21.stream.Part, music21.stream.Score
    """
    type_name=type(a).__name__
    #从对象类型到所调用函数的字典
    type_function_dict={
        "Dvsegment":lambda x:Dvtrack(name=x.name,segment=[copy.deepcopy(x)]),#dv区段对象
        "Dvtrack":copy.deepcopy,#dv音轨对象
        "Dvfile":lambda x:copy.deepcopy(x.track[track]),#dv工程对象
        "MidiTrack":lambda x:Dvtrack(name=x.name,segment=[to_dv_segment(x)]),#mido音轨对象
        "MidiFile":lambda x:Dvtrack(segment=[midi_track_to_dv_segment(x.tracks[track],ticks_per_beat=x.ticks_per_beats)],name=x.tracks[track].name),#mido文件对象
        "Stream":lambda x:Dvtrack(segment=[to_dv_segment(x)]),
        "Measure":lambda x:Dvtrack(segment=[to_dv_segment(x)]),
        "Part":lambda x:Dvtrack(segment=[to_dv_segment(x)]),
        "Score":lambda x:Dvtrack(segment=[to_dv_segment(x,track=track)])
    }
    #如果在这个字典中没有找到函数，则默认调用a.to_dv_track()
    return type_function_dict.get(type_name,lambda x:x.to_dv_track())(a)

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
        self.start:int=start
        self.length:int=length
        self.filename:str=filename
        self.name:str=name
        self.volume:int=volume
        #self.balance=balance
        self.mute:bool=mute
        self.solo:bool=solo

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
                 tempo:Union[List[Tuple[int,float]],float,int]=[(0,120.0)],
                 beats:List[Tuple[int,int,int]]=[(-3,4,4)],
                 track:List[Dvtrack]=[],
                 inst:List[Dvinst]=[]):
        if(type(tempo)!=list):
            tempo=[(0,float(tempo))]
        if(track==[]):
            track=[]
        if(inst==[]):
            inst=[]
        self.tempo:List[Tuple[int,float]]=tempo
        self.beats:List[Tuple[int,int,int]]=beats
        self.track:List[Dvtrack]=track
        self.inst:List[Dvinst]=inst
        
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
           +skwritelist([]+self.track+self.inst)[4:]
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
        将dv工程按照给定的分度值d（四分音符为480）量化。
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
    
    def cutparam(self,head:bool=True,tail:bool=True):
        """
        切去区段两端的无效参数
        head:是否切去区段开头的无效参数,bool
        tail:是否切去区段结尾的无效参数,bool
        """
        for seg in self.track:
            seg.cutparam(head=head,tail=tail)
        return self

    def fixnoteoverlap(self):
        """
        修复音符重叠
        起点相同的音符，保留音高最高的
        起点不同的重叠音符，截取前一个音符的重叠部分
        """
        for tr in self.track:
            tr.fixnoteoverlap()
        return self
    
    def fix(self):
        """
        自动修复工程：
        - 删除区段两端的无效音符和无效参数
        - 音符按开始时间排序
        - 修复音符重叠
        """
        for tr in self.track:
            tr.fix()
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

    def setsinger(self,singer:str):
        '''
        为工程中的所有区段统一设置音源名
        '''
        for tr in self.track:
            tr.setsinger(singer)
        return self

    def transpose(self,n:int):
        """
        对dv工程移调
        n：移调半音数，向上为正，向下为负。
        """
        for tr in self.track:
            tr.transpose(n)
        return self

    def to_midi_file(self,filename:str="",use_hanzi:bool=False):
        '''
        将dv文件对象转换为mid文件与mido.MidiFile对象
        默认使用dv文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        import mido
        mid = mido.MidiFile()
        #控制轨
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
            ust.tempo=tempo
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
        将dv文件按音轨转换为music21乐谱对象，并自动判断调性
        默认使用dv文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        import music21
        sc=music21.stream.Score()
        #音轨
        starttime=self.pos2tick(1)
        #求音轨长度
        length=max(i.segment[-1].start+i.segment[-1].length for i in self.track)-starttime
        #转换音轨
        for tr in self.track:
            u=sum(tr.segment,Dvsegment(start=starttime,length=0))
            u.length=length
            u=u.to_ust_file(use_hanzi=use_hanzi)
            u.tempo=0#阻止Ustfile将曲速写入music21对象，交由dvfile来写
            p=music21.stream.Part(u.to_music21_stream())
            p.partName=tr.name
            sc.append(p)
        #节拍
        beats=self.beats[0]
        ts=music21.meter.TimeSignature()
        ts.numerator=beats[1]#每小节拍数
        ts.denominator=beats[2]#音符分数
        for p in sc.parts:
            p.insert(0,ts)
        #曲速
        mm = music21.tempo.MetronomeMark(number=self.tempo[0][1])
        for p in sc.parts:
            p.insert(0,mm)
        return sc
    
    def to_iftp_file(self,use_hanzi:bool=False):
        #iftpy暂停开发，请勿使用
        import iftpy
        iftptracks=[]
        tempo=self.tempo[0][1]
        beat=self.beats[0][1]
        for tr in self.track:
            iftptracks.append(tr.to_iftp_track(use_hanzi=use_hanzi,beat=beat))
        return iftpy.Iftpfile(track=iftptracks,beat=beat).settempo(tempo)

def to_dv_file(a)->Dvfile:
    """
    将其他类型的音轨工程对象a转为dv工程对象
    支持对象类型：
    utaufile.Ustfile, utaufile.Nnfile, dvfile.Dvsegment, dvfile.Dvtrack, dvfile.Dvfile, mido.MidiTrack,
    mido.MidiFile, music21.stream.Stream, music21.stream.Measure, music21.stream.Part, music21.stream.Score
    """
    type_name=type(a).__name__
    #从对象类型到所调用函数的字典
    type_function_dict={
        "Dvsegment":lambda x:Dvfile(track=[Dvtrack(name=x.name,segment=[copy.deepcopy(x)])]),
        "Dvtrack":lambda x:Dvfile(track=[copy.deepcopy(x)]),
        "Dvfile":copy.deepcopy,
        "MidiTrack":lambda x:Dvfile(track=[to_dv_track(x)]),
        "MidiFile":lambda x:Dvfile(track=[Dvtrack(name=tr.name,segment=[midi_track_to_dv_segment(tr,ticks_per_beat=x.ticks_per_beat)]) for tr in x.tracks]),
        "Stream":lambda x:Dvfile(track=[to_dv_track(x)]),
        "Measure":lambda x:Dvfile(track=[to_dv_track(x)]),
        "Part":lambda x:Dvfile(track=[to_dv_track(x)]),
        "Score":lambda x:Dvfile(track=[to_dv_track(tr) for tr in x.parts]),
    }
    #如果在这个字典中没有找到函数，则默认调用a.to_dv_file()
    return type_function_dict.get(type_name,lambda x:x.to_dv_file())(a)

def opendv(filename:str)->Dvfile:
    '''
    打开sk或dv文件，返回Dvfile对象
    '''
    from dvfile.data import balanceread
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
            beats+=[(skreadint(file),skreadint(file),skreadint(file))]
        track=[]
        inst=[]
        for i in range(0,skreadint(file)):#读音轨
            tracktype=skreadint(file)#合成音轨0，伴奏1
            if(tracktype==0):#合成音轨
                trackname=skreadstr(file)
                mute=(file.read(1)==b'\x01')
                solo=(file.read(1)==b'\x01')
                volume=skreadint(file)
                balance=balanceread.get(file.read(4),0)#左右声道平衡
                file.read(4)#区段占用空间
                segment=[]
                for i in range(0,skreadint(file)):#读区段
                    segstart=skreadint(file)
                    seglength=skreadint(file)
                    segname=skreadstr(file)
                    singer=skreadstr(file)
                    file.read(4)#音符占用空间
                    note=[]
                    for i in range(0,skreadint(file)):#读音符
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
                        bendep=skreadint(file)#弯曲深度
                        benlen=skreadint(file)#弯曲长度
                        portail=skreadint(file)#尾部滑音长度
                        porhead=skreadint(file)#头部滑音长度
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
                    #音调Pitch，以音分为单位，转换成midi标准的100倍，0表示按默认音调
                    pit=numpy.fromfile(file,"<i4",skreadint(file)//4)[1:].reshape([-1,2])
                    sgn=(numpy.sign(pit[:,1])+1)//2
                    pit[:,1]=sgn*(11550-pit[:,1])
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
                                        singer,
                                        note,
                                        vol=vol,
                                        pit=pit,
                                        bre=bre,
                                        gen=gen)]
                track+=[Dvtrack(trackname,segment,volume,balance,mute,solo)]
            else:#伴奏音轨
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

def main():
    import mido
    m=mido.MidiFile(r"gthl.mid")
    d=to_dv_file(m)
    d.save(r"gthl.dv")
    
if(__name__=="__main__"):
    main()