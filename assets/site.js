(function(){
var $=function(i){return document.getElementById(i)},B=document.body,FS=B.getAttribute('data-fs'),GS=B.getAttribute('data-gs');
var m=$('menu'),b=$('mb');
if(m&&b){var t=function(o){m.classList.toggle('open',o);b.setAttribute('aria-expanded',o)};
b.onclick=function(e){e.stopPropagation();t(!m.classList.contains('open'))};m.onclick=function(e){e.stopPropagation()};
document.addEventListener('click',function(){t(false)});document.addEventListener('keydown',function(e){if(e.key==='Escape')t(false)});
if($('mc'))$('mc').onclick=function(){t(false)}}
var f=$('f');
if(f){var hp=document.createElement('input');hp.type='text';hp.name='_gotcha';hp.tabIndex=-1;hp.autocomplete='off';hp.style.cssText='position:absolute;left:-9999px';f.appendChild(hp);
f.addEventListener('submit',function(e){e.preventDefault();
var dt=f.querySelector('input[type=date]');
var d={_subject:'Nieuwe aanvraag — '+document.title.split('|')[0].trim()+(dt&&dt.value?' — '+dt.value.split('-').reverse().join('/'):''),pagina:location.href,dienst:f.getAttribute('data-dienst')||'',_gotcha:hp.value};
f.querySelectorAll('input[id],select[id],textarea[id]').forEach(function(x){if(!x.value)return;
if(x.type==='email'){d.email=x.value;return}
var l=document.querySelector('label[for="'+x.id+'"]');d[x.getAttribute('data-k')||(l?l.textContent:x.id)]=x.value});
if(!d.dienst)d.dienst=d['Gewenste dienst']||'Contact';
var bt=f.querySelector('button[type=submit]'),tx=bt.textContent;bt.disabled=true;bt.textContent='Bezig met verzenden...';
fetch(FS,{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify(d)}).then(function(r){if(!r.ok)throw 0;
if(GS)fetch(GS,{method:'POST',mode:'no-cors',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify(d)}).catch(function(){});
f.style.display='none';$('ty').style.display='block';$('ty').scrollIntoView({behavior:'smooth',block:'center'})}).catch(function(){bt.disabled=false;bt.textContent=tx;alert('Er liep iets fout. Probeer opnieuw of mail naar Bloom_byjana@outlook.com')})})}
})();
