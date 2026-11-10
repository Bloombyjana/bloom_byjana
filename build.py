"""Bouwt de website uit templates/ en data/ naar _site/. Draait automatisch via GitHub Actions."""
import os,shutil,json,yaml,markdown,glob
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
used=set()
for out,tpl,key,url,svc,fk in PAGES:
    p=D['paginas'][key] if key else {}
    title=p.get('titel') or ('Privacybeleid | BLOOM by Jana' if 'privacy' in url else 'Pagina niet gevonden | BLOOM by Jana')
    desc=p.get('beschrijving') or ('Hoe BLOOM by Jana omgaat met je gegevens.' if 'privacy' in url else 'Pagina niet gevonden.')
    og=p.get('hero_foto') or (p['hero_fotos'][0]['foto'] if p.get('hero_fotos') else '') or '/assets/img/hero-frame.jpg'
    html=env.get_template(tpl).render(D=D,s=s,p=p,page={'url':url,'noindex':url=='/404.html'},title=title,desc=desc,base=BASE,og_image=og,ld=ld(url,svc,fk,desc,key=='home') if key else None)
    path=os.path.join('_site',out);os.makedirs(os.path.dirname(path),exist_ok=True);open(path,'w',encoding='utf-8').write(html)
    import re;used|=set(re.findall(r'src="(/assets/img/[^"]+)"',html))
shutil.copytree('assets','_site/assets')
for f in glob.glob('public/*'):
    (shutil.copytree if os.path.isdir(f) else shutil.copy)(f,os.path.join('_site',os.path.basename(f)))
open('_site/sitemap.xml','w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'<url><loc>{BASE}{u}</loc></url>\n' for _,_,_,u,_,_ in PAGES if u!='/404.html')+'</urlset>\n')
miss=sorted(u for u in used if not os.path.exists(u[1:]))
print('Gebouwd:',len(PAGES),'pagina’s.')
if miss: print('Let op, foto’s nog niet geüpload (placeholder blijft staan):',', '.join(m.split('/')[-1] for m in miss))
