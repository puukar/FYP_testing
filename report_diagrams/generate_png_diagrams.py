"""Generate five dependency-free PNG diagrams for the FYP report."""
import os, struct, zlib

OUT = os.path.dirname(__file__)
WHITE=(255,255,255); INK=(28,45,72); BLUE=(226,239,253); GREEN=(229,245,235); YELLOW=(255,247,211); GREY=(245,247,250); RED=(255,235,235)

FONT = {
'A':["01110","10001","10001","11111","10001","10001","10001"], 'B':["11110","10001","10001","11110","10001","10001","11110"], 'C':["01111","10000","10000","10000","10000","10000","01111"], 'D':["11110","10001","10001","10001","10001","10001","11110"], 'E':["11111","10000","10000","11110","10000","10000","11111"], 'F':["11111","10000","10000","11110","10000","10000","10000"], 'G':["01111","10000","10000","10111","10001","10001","01110"], 'H':["10001","10001","10001","11111","10001","10001","10001"], 'I':["11111","00100","00100","00100","00100","00100","11111"], 'J':["00111","00010","00010","00010","10010","10010","01100"], 'K':["10001","10010","10100","11000","10100","10010","10001"], 'L':["10000","10000","10000","10000","10000","10000","11111"], 'M':["10001","11011","10101","10101","10001","10001","10001"], 'N':["10001","11001","10101","10011","10001","10001","10001"], 'O':["01110","10001","10001","10001","10001","10001","01110"], 'P':["11110","10001","10001","11110","10000","10000","10000"], 'Q':["01110","10001","10001","10001","10101","10010","01101"], 'R':["11110","10001","10001","11110","10100","10010","10001"], 'S':["01111","10000","10000","01110","00001","00001","11110"], 'T':["11111","00100","00100","00100","00100","00100","00100"], 'U':["10001","10001","10001","10001","10001","10001","01110"], 'V':["10001","10001","10001","10001","10001","01010","00100"], 'W':["10001","10001","10001","10101","10101","10101","01010"], 'X':["10001","10001","01010","00100","01010","10001","10001"], 'Y':["10001","10001","01010","00100","00100","00100","00100"], 'Z':["11111","00001","00010","00100","01000","10000","11111"], '0':["01110","10001","10011","10101","11001","10001","01110"], '1':["00100","01100","00100","00100","00100","00100","01110"], '2':["01110","10001","00001","00010","00100","01000","11111"], '3':["11110","00001","00001","01110","00001","00001","11110"], '4':["00010","00110","01010","10010","11111","00010","00010"], '5':["11111","10000","10000","11110","00001","00001","11110"], '6':["01110","10000","10000","11110","10001","10001","01110"], '7':["11111","00001","00010","00100","01000","01000","01000"], '8':["01110","10001","10001","01110","10001","10001","01110"], '9':["01110","10001","10001","01111","00001","00001","01110"], '-':["00000","00000","00000","11111","00000","00000","00000"], ' ':["00000"]*7, '/':["00001","00010","00100","01000","10000","00000","00000"], ':':["00000","00100","00100","00000","00100","00100","00000"], '(':["00010","00100","01000","01000","01000","00100","00010"], ')':["01000","00100","00010","00010","00010","00100","01000"], '.':["00000","00000","00000","00000","00000","00100","00100"]}

class Canvas:
    def __init__(self,w,h): self.w=w; self.h=h; self.p=[bytearray(WHITE*w) for _ in range(h*3)]
    def px(self,x,y,c=INK):
        if 0<=x<self.w and 0<=y<self.h:
            i=y*3; self.p[i][x]=c[0]; self.p[i+1][x]=c[1]; self.p[i+2][x]=c[2]
    def fill(self,x,y,w,h,c):
        for yy in range(max(0,y),min(self.h,y+h)):
            row=yy*3
            self.p[row][max(0,x):min(self.w,x+w)]=bytes([c[0]])*max(0,min(self.w,x+w)-max(0,x))
            self.p[row+1][max(0,x):min(self.w,x+w)]=bytes([c[1]])*max(0,min(self.w,x+w)-max(0,x))
            self.p[row+2][max(0,x):min(self.w,x+w)]=bytes([c[2]])*max(0,min(self.w,x+w)-max(0,x))
    def line(self,x1,y1,x2,y2,c=INK,t=2):
        dx=abs(x2-x1); sx=1 if x1<x2 else -1; dy=-abs(y2-y1); sy=1 if y1<y2 else -1; e=dx+dy
        while True:
            for ox in range(-(t//2),t//2+1):
                for oy in range(-(t//2),t//2+1): self.px(x1+ox,y1+oy,c)
            if x1==x2 and y1==y2: break
            e2=2*e
            if e2>=dy: e+=dy; x1+=sx
            if e2<=dx: e+=dx; y1+=sy
    def rect(self,x,y,w,h,fill=GREY):
        self.fill(x,y,w,h,fill); self.line(x,y,x+w,y); self.line(x+w,y,x+w,y+h); self.line(x+w,y+h,x,y+h); self.line(x,y+h,x,y)
    def arrow(self,x1,y1,x2,y2,label=None):
        self.line(x1,y1,x2,y2); dx=x2-x1; dy=y2-y1
        if abs(dx)>=abs(dy):
            s=1 if dx>=0 else -1; self.line(x2,y2,x2-12*s,y2-7); self.line(x2,y2,x2-12*s,y2+7)
        else:
            s=1 if dy>=0 else -1; self.line(x2,y2,x2-7,y2-12*s); self.line(x2,y2,x2+7,y2-12*s)
        if label: self.text((x1+x2)//2, (y1+y2)//2-14, label, 2, center=True)
    def text(self,x,y,s,scale=2,c=INK,center=False):
        s=s.upper()
        if center: x-=len(s)*6*scale//2
        for ch in s:
            glyph=FONT.get(ch,FONT[' '])
            for gy,row in enumerate(glyph):
                for gx,v in enumerate(row):
                    if v=='1': self.fill(x+gx*scale,y+gy*scale,scale,scale,c)
            x+=6*scale
    def save(self,path):
        raw=b''.join(b'\0'+bytes(self.p[y*3])+bytes(self.p[y*3+1])+bytes(self.p[y*3+2]) for y in range(self.h))
        def chunk(tag,data): return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
        png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',self.w,self.h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b'')
        with open(path,'wb') as f: f.write(png)

def title(c,s): c.text(c.w//2,35,s,4,center=True); c.line(70,80,c.w-70,80,INK,1)
def box(c,x,y,w,h,head,items,colour=BLUE):
    c.rect(x,y,w,h,colour); c.fill(x,y,w,31,INK); c.text(x+w//2,y+8,head,2,WHITE,True)
    for i,item in enumerate(items): c.text(x+13,y+43+i*20,item,2)

def class_diagram():
    c=Canvas(1800,1200); title(c,'CLASS DIAGRAM - RESUME ANALYZER')
    box(c,70,130,310,160,'USER',['ID','EMAIL','FULL NAME'],GREEN)
    box(c,70,430,310,210,'RESUME',['ID','USER ID','FILENAME','FILE TYPE','PARSED SKILLS'],BLUE)
    box(c,70,810,310,210,'SKILL GAP',['ID','RESUME ID','TARGET ROLE','MATCH SCORE'],YELLOW)
    box(c,590,130,310,190,'AUTH SERVICE',['SIGN UP','SIGN IN','SIGN OUT'],GREY)
    box(c,590,430,310,220,'RESUME REPOSITORY',['SAVE RESUME','GET RESUMES','SAVE ANALYSIS'],GREY)
    box(c,1080,130,310,210,'SKILL REPOSITORY',['GET JOB ROLES','GET SKILLS','SEARCH SKILLS'],GREY)
    box(c,1080,500,310,210,'RESUME PARSER',['PARSE RESUME','PARSE PDF','EXTRACT DOCX'],GREY)
    box(c,1480,400,250,210,'SKILL MATCHER',['ANALYZE RESUME','COMPUTE GAP','NORMALIZE SKILL'],GREY)
    box(c,1080,850,310,180,'JOB ROLE',['ROLE NAME','REQUIRED SKILLS'],GREEN)
    c.arrow(225,290,225,430,'UPLOADS'); c.arrow(225,640,225,810,'GENERATES')
    c.arrow(380,215,590,215,'MANAGES'); c.arrow(380,540,590,540,'MANAGES')
    c.arrow(900,540,1080,605,'USES'); c.arrow(1390,605,1480,505,'USES')
    c.arrow(1235,710,1235,850,'COMPARES'); c.arrow(1390,235,1480,465,'PROVIDES')
    c.save(os.path.join(OUT,'01_class_diagram.png'))

def object_diagram():
    c=Canvas(1600,950); title(c,'OBJECT DIAGRAM - EXAMPLE RESUME ANALYSIS')
    box(c,80,180,330,200,'USER1 : USER',['ID: U001','EMAIL: SAMIR@EXAMPLE.COM','NAME: SAMIR SHARMA'],GREEN)
    box(c,80,570,330,220,'RESUME1 : RESUME',['ID: R001','FILE: SAMIR RESUME PDF','SKILLS: PYTHON SQL PANDAS'],BLUE)
    box(c,620,570,370,220,'ANALYSIS1 : SKILL GAP',['ROLE: JUNIOR DATA SCIENTIST','MATCHED: PYTHON SQL PANDAS','SCORE: 50 PERCENT'],YELLOW)
    box(c,1120,180,360,230,'ROLE1 : JOB ROLE',['NAME: JUNIOR DATA SCIENTIST','REQUIRED: PYTHON SQL PANDAS','NUMPY STATISTICS ML'],GREEN)
    c.arrow(245,380,245,570,'UPLOADS'); c.arrow(410,680,620,680,'GENERATES'); c.arrow(990,650,1120,380,'EVALUATES'); c.arrow(410,280,1120,280,'SELECTS')
    c.save(os.path.join(OUT,'02_object_diagram.png'))

def state_diagram():
    c=Canvas(1800,900); title(c,'STATE DIAGRAM - RESUME ANALYSIS LIFECYCLE')
    states=[('UPLOADED',100,390,BLUE),('VALIDATING',350,390,BLUE),('EXTRACTING TEXT',620,390,BLUE),('PARSING RESUME',930,390,BLUE),('SKILL MATCHING',1240,390,BLUE),('SAVED AND DISPLAYED',1510,390,GREEN)]
    for label,x,y,col in states: box(c,x,y,210,90,label,[],col)
    for i in range(len(states)-1): c.arrow(states[i][1]+210,435,states[i+1][1],435)
    box(c,350,650,210,80,'INVALID FILE',[],RED); box(c,620,650,230,80,'EXTRACTION FAILED',[],RED)
    c.arrow(455,480,455,650,'INVALID'); c.arrow(725,480,735,650,'FAILED')
    c.text(100,180,'START',3,center=True); c.arrow(145,220,145,390)
    c.text(1720,180,'END',3,center=True); c.arrow(1615,390,1720,220)
    c.save(os.path.join(OUT,'03_state_diagram.png'))

def sequence_diagram():
    c=Canvas(1800,1150); title(c,'SEQUENCE DIAGRAM - UPLOAD AND ANALYZE RESUME')
    actors=['USER','STREAMLIT UI','UPLOAD MODULE','SKILL MATCHER','RESUME PARSER','DATABASE']
    xs=[110,420,720,1020,1320,1620]
    for x,a in zip(xs,actors): box(c,x-100,115,200,55,a,[],GREEN if a in ('USER','DATABASE') else BLUE); c.line(x,170,x,1080,(110,130,155),1)
    steps=[(0,1,'UPLOAD RESUME'),(1,2,'SEND FILE'),(2,3,'ANALYZE RESUME'),(3,4,'PARSE RESUME'),(4,3,'EXTRACTED DATA'),(3,5,'GET ROLES AND SKILLS'),(5,3,'ROLE DATA'),(3,2,'ANALYSIS RESULT'),(2,5,'SAVE RESUME AND GAP'),(2,1,'DISPLAY RESULT'),(1,0,'VIEW RESULT')]
    y=230
    for a,b,label in steps:
        c.arrow(xs[a],y,xs[b],y,label); y+=72
    c.save(os.path.join(OUT,'04_sequence_diagram.png'))

def activity_diagram():
    c=Canvas(1200,1400); title(c,'ACTIVITY DIAGRAM - RESUME ANALYSIS PROCESS')
    flow=[('START',GREEN),('USER LOGS IN',BLUE),('UPLOAD RESUME',BLUE),('VALIDATE FILE',BLUE),('EXTRACT TEXT',BLUE),('PARSE SKILLS EDUCATION EXPERIENCE',BLUE),('RETRIEVE JOB ROLES',BLUE),('CALCULATE SKILL GAP AND SCORE',YELLOW),('SAVE RESUME AND ANALYSIS',BLUE),('DISPLAY RESULTS',GREEN),('END',GREEN)]
    y=115
    for i,(label,col) in enumerate(flow):
        box(c,370,y,460,65,label,[],col)
        if i<len(flow)-1: c.arrow(600,y+65,600,y+105)
        y+=105
    box(c,70,460,230,70,'SHOW ERROR',[],RED); c.arrow(370,500,300,500,'INVALID')
    box(c,900,565,240,70,'SHOW FAILURE',[],RED); c.arrow(830,605,900,605,'FAILED')
    c.save(os.path.join(OUT,'05_activity_diagram.png'))

if __name__ == '__main__':
    class_diagram(); object_diagram(); state_diagram(); sequence_diagram(); activity_diagram()
    print('Created five PNG diagram files in', OUT)
