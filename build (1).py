"""Bouwt de website uit templates/ en data/ naar _site/. Draait automatisch via GitHub Actions."""
import os,re,time,shutil,json,subprocess,yaml,markdown,glob
from collections import defaultdict
from PIL import Image,ImageOps
from jinja2 import Environment,FileSystemLoader,select_autoescape
from markupsafe import Markup
BASE='https://www.bloombyjana.com'
D={f[:-4]:yaml.safe_load(open('data/'+f,encoding='utf-8')) for f in os.listdir('data') if f.endswith('.yml')}
s=D['site']
env=Environment(loader=FileSystemLoader('templates'),autoescape=select_autoescape(['html']),trim_blocks=True,lstrip_blocks=True)
env.filters['md']=lambda t:Markup(markdown.markdown(t or ''))
PAGES=[('index.html','home.html','home','/',None,None),
('the-bloom-frame/index.html','frame.html','frame','/the-bloom-frame/','The Bloom Frame','frame'),
('the-bloom-bar/index.html','bar.html','bar','/the-bloom-bar/','The Bloom Bar','bar'),
('the-bloom-florals/index.html','florals.html','florals','/the-bloom-florals/','The Bloom Florals','florals'),
('the-face-behind-bloom/index.html','face.html','face','/the-face-behind-bloom/',None,None),
('contact/index.html','contact.html','contact','/contact/',None,None),
('privacy/index.html','privacy.html',None,'/privacy/',None,None),
('404.html','notfound.html',None,'/404.html',None,None)]
def ld(url,svc,fk,desc,home=False):
    biz={"@type":"Florist","@id":BASE+"/#business","name":s['naam'],"url":BASE+"/","description":s['omschrijving'],"slogan":"Your day. Your flowers. Your story.","email":s['email'],"address":{"@type":"PostalAddress","addressLocality":s['plaats'],"addressRegion":"Limburg","addressCountry":"BE"},"sameAs":[s['instagram']],"priceRange":"€€","areaServed":{"@type":"GeoCircle","geoMidpoint":{"@type":"GeoCoordinates","latitude":51.2333,"longitude":5.4167},"geoRadius":"50000"}}
    g=[biz]
    if home: g.append({"@type":"WebSite","name":s['naam'],"url":BASE+"/","inLanguage":"nl-BE"})
    if svc: g.append({"@type":"Service","name":svc,"provider":{"@id":BASE+"/#business"},"url":BASE+url,"description":desc})
    if fk and D['faq'].get(fk): g.append({"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q['vraag'],"acceptedAnswer":{"@type":"Answer","text":q['antwoord']}} for q in D['faq'][fk]]})
    return Markup(json.dumps({"@context":"https://schema.org","@graph":g},ensure_ascii=False).replace('<','\\u003c'))
shutil.rmtree('_site',ignore_errors=True);os.makedirs('_site')
shutil.copytree('assets','_site/assets',ignore=shutil.ignore_patterns('img'))
FOLDERS=['hero/home','hero/frame','hero/bar','hero/florals','hero/face','hero/contact','galerij/frame','galerij/bar','galerij/florals','galerij/face','portret','categorie/bridal','categorie/ceremony','categorie/table','categorie/venue']
EXT=('.jpg','.jpeg','.png','.webp')
def stamp(path):
    try:
        t=subprocess.run(['git','log','-1','--format=%ct','--',path],capture_output=True,text=True).stdout.strip()
        if t: return int(t)
    except Exception: pass
    return int(os.path.getmtime(path))
def process(folder):
    src='assets/img/'+folder;out=[];used=set()
    if not os.path.isdir(src): return out
    files=[f for f in os.listdir(src) if f.lower().endswith(EXT)]
    files.sort(key=lambda f:(-stamp(os.path.join(src,f)),f.lower()))   # nieuwste eerst
    for f in files:
        try: im=ImageOps.exif_transpose(Image.open(os.path.join(src,f))).convert('RGB')
        except Exception as e: print('Foto overgeslagen (niet leesbaar):',folder+'/'+f);continue
        slug=re.sub(r'[^a-z0-9]+','-',os.path.splitext(f)[0].lower()).strip('-') or 'foto'
        while slug in used: slug+='-2'
        used.add(slug)
        ws=sorted({w for w in (600,1200,2000) if w<im.width}|{min(im.width,2000)});urls=[]
        for w in ws:
            o=im if w==im.width else im.resize((w,round(im.height*w/im.width)),Image.LANCZOS)
            rel=f'assets/img/{folder}/{slug}-{w}.webp';os.makedirs(os.path.dirname('_site/'+rel),exist_ok=True)
            o.save('_site/'+rel,'WEBP',quality=82,method=4);urls.append((w,'/'+rel))
        out.append({'src':urls[-1][1],'srcset':', '.join(f'{u} {w}w' for w,u in urls),'w':im.width,'h':im.height,'_im':im if not out and folder=='hero/home' else None})
    return out
PH=defaultdict(list)
for fo in FOLDERS: PH[fo]=process(fo)
OG=''
if PH['hero/home']:
    im=PH['hero/home'][0].pop('_im');im.thumbnail((1200,1200));im.save('_site/assets/img/og.jpg','JPEG',quality=85);OG='/assets/img/og.jpg'
for v in PH.values():
    for x in v: x.pop('_im',None)
for out,tpl,key,url,svc,fk in PAGES:
    p=D['paginas'][key] if key else {}
    title=p.get('titel') or ('Privacybeleid | BLOOM by Jana' if 'privacy' in url else 'Pagina niet gevonden | BLOOM by Jana')
    desc=p.get('beschrijving') or ('Hoe BLOOM by Jana omgaat met je gegevens.' if 'privacy' in url else 'Pagina niet gevonden.')
    og=OG
    html=env.get_template(tpl).render(D=D,s=s,p=p,PH=PH,ver=str(int(time.time())),page={'url':url,'noindex':url=='/404.html'},title=title,desc=desc,base=BASE,og_image=og,ld=ld(url,svc,fk,desc,key=='home') if key else None)
    path=os.path.join('_site',out);os.makedirs(os.path.dirname(path),exist_ok=True);open(path,'w',encoding='utf-8').write(html)
for f in glob.glob('public/*'):
    (shutil.copytree if os.path.isdir(f) else shutil.copy)(f,os.path.join('_site',os.path.basename(f)))
open('_site/sitemap.xml','w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'<url><loc>{BASE}{u}</loc></url>\n' for _,_,_,u,_,_ in PAGES if u!='/404.html')+'</urlset>\n')
print('Gebouwd:',len(PAGES),'pagina’s;',sum(len(v) for v in PH.values()),'foto’s verwerkt.')
