__version__='0.0.4'

import copy
import numpy
from utaufile import Ustfile,Ustnote

def skreadint(file):
    return numpy.fromfile(file,"<i4",1)[0]

def skreadbytes(file):
    return file.read(skreadint(file))

def skreadstr(file):
    try:
        return str(skreadbytes(file),encoding="utf8")
    except:
        return ""

def intquantize(n,d:int)->int:
    return int(n/d+0.5)*d

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
                 vibamp=numpy.array([[-1,0],[0,0],[0,0],[100000,0],[100000,0],[100001,0]]),
                 vibfre=numpy.array([[-1,0],[0,0],[0,0],[100000,0],[100000,0],[100001,0]]),
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
    
class Dvsegment():
    '''
    dv区段类
    start:起点，480为一拍，从-3小节算起，int
    length:长度，480为一拍，int
    name:区段名，str
    vbname:音源名，str
    note:音符列表
    '''
    def __init__(self,start:int,
                 length:int,
                 name:str="",
                 vbname:str="",
                 note:list=[]):
        if(note==[]):
            note=[]
        self.start=start
        self.length=length
        self.name=name
        self.vbname=vbname
        self.note=note
        
    def __str__(self):
        s="  segment {} {} {} {}\n".format(
            self.start,
            self.length,
            self.name,
            self.vbname)
        for i in self.note:
            s+=str(i)
        return s
    
    def __add__(self,other):
        #两个区段相加可合并区段
        #self为上一区段，other为下一区段
        deltatime=other.start-self.start#时间差
        seg=Dvsegment(start=self.start,
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
    
    def to_ust_file(self,use_hanzi:bool=False):
        '''
        将dv区段对象转换为ust文件对象
        默认使用dv文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
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
    
    def to_ust_file(self,use_hanzi:bool=False):
        '''
        将dv音轨对象转换为ust文件对象
        默认使用dv文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        s=sum(self.segment,Dvsegment(0,0))
        return s.to_ust_file(use_hanzi)
    
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
    filename:文件名
    name:伴奏音轨名
    volume:音量
    mute:静音
    solo:独奏
    '''
    def __init__(self,
                 start:int,
                 filename:str="",
                 name:str="",
                 volume:int=30,
                 mute:bool=False,
                 solo:bool=False,
                 ):
        self.name=name
        self.volume=volume
        #self.balance=balance
        self.mute=mute
        self.solo=solo

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
                 tempo:list=[(0,120.0)],
                 beats:list=[(-3,4,4)],
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
    
    def tick2pos(self,tick:int)->tuple:
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
    
    def cut(head=True,tail=True):
        '''
        对工程中的每个区段，切去开始时间为负数的音符，以及结束时间大于区段长度的音符
        （这些音符在deepvocal编辑器中是无效音符）
        head:是否切去开始时间为负数的音符,bool
        tail:是否切去结束时间大于区段长度的音符,bool
        '''
        for tr in self.track():
            tr.cut(head=head,tail=tail)
    
    def to_ust_file(self,use_hanzi:bool=False)->list:
        '''
        将dv文件按音轨转换为ust文件对象的列表
        默认使用dv文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        usts=[]
        for track in self.track:
            ust=track.to_ust_file(use_hanzi)
            ust.properties["Tempo"]=self.tempo[0][1]
            usts+=[ust]
        return usts
    
    def to_music21_score(self,use_hanzi:bool=False):
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
                        file.read(4)
                        pinyin=skreadstr(file)
                        hanzi=skreadstr(file)
                        file.read(1)
                        #以下是数据块1,包含颤音幅度线和颤音速度线
                        data1=numpy.fromfile(file,"<i4",skreadint(file)//4)#未知数据块1,包含滑音幅度线和频率线
                        vibamp=data1[2:2+data1[1]*2].reshape([-1,2])#颤音幅度线
                        data1=data1[2+data1[1]*2:]
                        vibfre=data1[2:2+data1[1]*2].reshape([-1,2])#颤音速度线
                        data1=data1[2+data1[1]*2:]
                        vibp=data1[2:2+data1[1]*2].reshape([-1,2])#渲染出的颤音音高曲线
                        #以上是未知数据块2
                        data2=numpy.fromfile(file,"<i4",skreadint(file)//4)#未知数据块2###
                        file.read(2)
                        file.read(16)#音素
                        benlen=skreadint(file)#弯曲长度
                        bendep=skreadint(file)#弯曲深度
                        porhead=skreadint(file)#头部滑音长度
                        portail=skreadint(file)#尾部滑音长度
                        timbre=skreadint(file)#音阶
                        crolrc=skreadstr(file)#交叉拼音
                        crotim=skreadint(file)#交叉音阶
                        note+=[Dvnote(start,length,notenum,pinyin,hanzi,
                                      benlen,bendep,porhead,portail,
                                      timbre,vibamp,vibfre,vibp,crolrc,crotim)]
                    #以下是音轨参数
                    skreadbytes(file)
                    skreadbytes(file)
                    skreadbytes(file)
                    skreadbytes(file)
                    skreadbytes(file)
                    skreadbytes(file)
                    skreadbytes(file)
                    segment+=[Dvsegment(segstart,seglength,segname,vbname,note)]
                track+=[Dvtrack(trackname,segment,volume,mute,solo)]
            else:
                trackname=skreadstr(file)
                mute=(file.read(1)==b'\x01')
                solo=(file.read(1)==b'\x01')
                volume=skreadint(file)
                file.read(4)
                file.read(4)
                skreadint(file)
                segstart=skreadint(file)
                seglength=skreadint(file)
                skreadstr(file)
                fname=skreadstr(file)
                inst+=[Dvinst(segstart,fname,trackname,volume,mute,solo)]
    return Dvfile(tempo=tempo,beats=beats,track=track,inst=inst)

def main():
    pass

if(__name__=="__main__"):
    main()