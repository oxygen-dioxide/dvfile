__version__='0.0.1'

import copy
import numpy
from utaufile import Ustfile,Ustnote
from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo

def skreadint(file):
    return numpy.fromfile(file,"<i4",1)[0]

def skreadbytes(file):
    return file.read(skreadint(file))

def skreadstr(file):
    return str(skreadbytes(file),encoding="utf8")

class Dvnote():
    '''
    dv音符类    
    start:起点，480为一拍，int
    length:长度，480为一拍，int
    notenum:音高，与midi相同，即C4为60，音高越高，数值越大，int
    hanzi:歌词汉字，str
    pinyin:歌词拼音，str
    '''
    def __init__(self,start:int,
                 length:int,
                 notenum:int,
                 pinyin:str,
                 hanzi:str):
        self.start=start
        self.length=length
        self.notenum=notenum
        self.pinyin=pinyin
        self.hanzi=hanzi
    
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
        self.start=start
        self.length=length
        self.name=name
        self.vbname=vbname
        self.note=note
        
    def __str__(self):
        s="  {} {} {} {}\n".format(
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
        track=MidiTrack()
        time=0
        for note in self.note:
            if(use_hanzi):
                track.append(MetaMessage('lyrics',text=note.hanzi,time=(note.start-time)))
            else:
                track.append(MetaMessage('lyrics',text=note.pinyin,time=(note.start-time)))
            track.append(Message('note_on', note=note.notenum,velocity=64,time=0))
            track.append(Message('note_off',note=note.notenum,velocity=64,time=note.length))
            time=note.start+note.length
        track.append(MetaMessage('end_of_track'))
        return track
    
    def sort(self):
        '''
        音符按开始时间排序
        '''
        def sortkey(note):
            return note.start
        self.note=sorted(self.note,key=sortkey)
        return self
        
    def cut(self,head=True,tail=True):
        '''
        切去开始时间为负数的音符，以及结束时间大于区段长度的音符
        （这些音符在deepvocal编辑器中是无效音符）
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
        
    def to_ust_file(self,use_hanzi:bool=False):
        '''
        将dv音轨对象转换为ust文件对象
        默认使用dv文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        s=sum(self.segment,Dvsegment(0,0))
        return s.to_ust_file()
    
    def to_midi_track(self,use_hanzi:bool=False):
        '''
        将dv音轨对象转换为mido.MidiTrack文件对象
        默认使用dv文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        s=sum(self.segment,Dvsegment(0,0))
        return s.to_midi_track()
        
class Dvfile():
    '''
    dv文件类
    tempo:曲速标记列表，
        曲速标记：(位置,曲速)
    beats:节拍标记列表
        节拍标记：(小节数位置,每小节拍数,x分音符为1拍)
    track:音轨列表
    '''
    def __init__(self,tempo:list=[],beats:list=[],track:list=[]):
        self.tempo=tempo
        self.beats=beats
        self.track=track
        
    def __str__(self):
        s="{}\n{}\n".format(self.tempo,self.beats)
        for i in self.track:
            s+=str(i)
        return s
        
    def to_midi_file(self,filename:str="",use_hanzi:bool=False):
        '''
        将dv文件对象转换为mid文件与mido.MidiFile对象
        默认使用dv文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        mid = MidiFile()
        ctrltrack=MidiTrack()
        ctrltrack.append(MetaMessage('track_name',name='Control',time=0))
        tick=0
        for i in self.tempo:
            ctrltrack.append(MetaMessage('set_tempo',tempo=bpm2tempo(i[1]),time=i[0]-tick))
            tick=i[0]
        mid.tracks.append(ctrltrack)
        for i in self.track:
            mid.tracks.append(i.to_midi_track(use_hanzi=use_hanzi))
        if(filename!=""):
            mid.save(filename)
        return mid
    
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
        for i in range(0,skreadint(file)):
            #读音轨
            tracktype=skreadint(file)#合成音轨0，伴奏1
            if(tracktype==0):
                trackname=skreadstr(file)
                file.read(2)
                volume=skreadint(file)
                file.read(4)#balance
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
                        note+=[Dvnote(start,length,notenum,pinyin,hanzi)]
                        file.read(1)
                        skreadbytes(file)
                        skreadbytes(file)
                        file.read(2)
                        file.read(16)#音素
                        benlen=skreadint(file)#弯曲长度
                        bendep=skreadint(file)#弯曲深度
                        porhead=skreadint(file)#头部滑音长度
                        portail=skreadint(file)#尾部滑音长度
                        timbre=skreadint(file)#音阶
                        cross=skreadstr(file)#交叉
                        crotim=skreadint(file)#交叉音阶
                    skreadbytes(file)
                    skreadbytes(file)
                    skreadbytes(file)
                    skreadbytes(file)
                    skreadbytes(file)
                    skreadbytes(file)
                    skreadbytes(file)
                    segment+=[Dvsegment(segstart,seglength,segname,vbname,note)]
                track+=[Dvtrack(trackname,segment,volume)]
            else:
                skreadbytes(file)
                file.read(2)
                skreadint(file)
                skreadint(file)
                skreadbytes(file)
    return Dvfile(tempo=tempo,beats=beats,track=track)

if(__name__=="__main__"):
    print(opendv(r'C:/Users/lin/Desktop/1.dv'))
    