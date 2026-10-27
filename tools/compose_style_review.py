"""Unretouched game-asset renders and actual Godot frames for visual review."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import numpy as np
ROOT=Path(__file__).resolve().parents[1];SRC=Path('/workspace/deliverables/style_pass');OUT=Path('/workspace/deliverables')
font='/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf';regular='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
ink='#342d31';muted='#7b6b64';red='#9f2d2a'
def canvas(w,h):
 return Image.new('RGBA',(w,h),(232,223,207,255))

def text(board,x,y,s,size=22,color=ink):ImageDraw.Draw(board).text((x,y),s,fill=color,font=ImageFont.truetype(font,size))
def centered(board,x,y,s,size=22,color=ink):
 d=ImageDraw.Draw(board);f=ImageFont.truetype(font,size);d.text((x-d.textlength(s,font=f)/2,y),s,font=f,fill=color)
def title(board,label,sub):
 d=ImageDraw.Draw(board);w,h=board.size;d.rectangle((68,60,84,182),fill=red)
 text(board,110,53,'PAM',96);text(board,115,157,'PUNCH FOREVER',24,red)
 text(board,w-850,83,label,26);text(board,w-850,126,sub,20,muted)
 d.line((106,220,w-106,220),fill='#c3b59f',width=2)
board=canvas(2800,1450);title(board,'ELENCO DA FASE 1','Modelos 3D • direção visual baseada no Pam aprovado')
for key,x,height,label,role in [('jaburanga',470,920,'JABURANGA','Mestre'),('assassin',1190,940,'ASSASSINO','Identidade oculta'),('guardian',1820,820,'GUARDIÃO DO JATOBÁ','Guardião das ruínas'),('guardian_scout',2410,820,'SENTINELA DO IGARAPÉ','Guardião das ruínas')]:
 im=Image.open(SRC/(key+'.png')).convert('RGBA');im=im.crop(im.getchannel('A').getbbox());im=im.resize((round(im.width*height/im.height),height),Image.Resampling.LANCZOS)
 baseline=1250;sh=Image.new('RGBA',board.size);sd=ImageDraw.Draw(sh);sd.ellipse((x-im.width*.28,baseline-9,x+im.width*.28,baseline+11),fill=(50,40,33,25));board.alpha_composite(sh.filter(ImageFilter.GaussianBlur(15)))
 board.alpha_composite(im,(int(x-im.width/2),baseline-height));centered(board,x,1305,label,24);centered(board,x,1345,role,20,muted)
board.convert('RGB').save(OUT/'Pam_Elenco_Fase1.png');board.convert('RGB').save(ROOT/'docs/captures/elenco-fase1.png')
# The world sheet contains actual captures of the game, with staged review cameras.
board=canvas(2520,1920);title(board,'A TRILHA DA VINGANÇA','Capturas no Godot 4.4.1 • câmera preparada para revisão de arte')
frames=[('floresta_e_mestre','FLORESTA E PERSONAGENS'),('ruinas_e_travessia','RUÍNAS E TRAVESSIA'),('altar_detalhe','ALTAR DAS RAÍZES'),('guardioes_na_trilha','GUARDIÕES NA TRILHA')]
for i,(key,label) in enumerate(frames):
 x=90+(i%2)*1230;y=280+(i//2)*820
 im=Image.open(SRC/(key+'.png')).convert('RGB');im=im.resize((1152,720),Image.Resampling.LANCZOS)
 board.paste(im,(x,y));text(board,x,y+742,label,23)
board.convert('RGB').save(OUT/'Pam_Cenario_Fase1.png');board.convert('RGB').save(ROOT/'docs/captures/cenario-fase1.png')
print('CAST_AND_WORLD_REVIEW_COMPLETE')
