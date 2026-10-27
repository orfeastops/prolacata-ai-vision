"""Offline time-coded review page; no server or uploads needed."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v4'

HTML=r'''<!doctype html><html lang="el"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Φέτα — 6 αποσπάσματα για επιβεβαίωση</title>
<style>
body{font:16px system-ui;margin:0;background:#101827;color:#ecf2fa}main{max-width:1300px;margin:auto;padding:20px}
h1{font-size:25px;margin:0 0 10px}p{line-height:1.5;color:#c2cede}.bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:12px 0}
button,select,input{font:inherit;padding:10px;border-radius:7px;border:1px solid #42536e;background:#1d2c44;color:white}button{cursor:pointer}
button:hover{background:#324967}.primary{background:#166554}video{display:block;width:100%;max-height:68vh;background:black}
.clock{font:700 24px ui-monospace;color:#7dd3fc}.form{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;background:#17243a;padding:15px;border-radius:10px}
label{display:grid;gap:6px}input{min-width:0}table{border-collapse:collapse;width:100%;margin-top:18px}td,th{padding:10px;text-align:left;border-bottom:1px solid #344156}
.muted{font-size:14px;color:#a9b8ce}.message{min-height:26px;color:#fbbf24}a{color:#7dd3fc}.note{border-left:3px solid #38bdf8;padding-left:12px}
</style><main><h1>6 νέα αποσπάσματα — σημειώνουμε τι πραγματικά συμβαίνει</h1>
<p>Για κάθε μεταφορά γράψε <b>πόσα μπλοκ</b>, πότε <b>σηκώνονται</b> και πότε <b>αφήνονται</b>. Η διάρκεια υπολογίζεται αυτόματα. Αν δεν φαίνεται κάτι, άφησέ το άγνωστο. Δεν υποθέτουμε 2 ανά κίνηση ή 10 ανά παλέτα.</p>
<div class="bar"><label>Απόσπασμα <select id="clip"></select></label><span id="source" class="muted"></span></div>
<video id="video" controls preload="metadata"></video>
<div class="bar"><button id="prev">◀ Καρέ</button><button id="play">Παύση / Συνέχεια</button><button id="next">Καρέ ▶</button>
<label>Ταχύτητα <select id="speed"><option value="0.25">0,25×</option><option value="0.5">0,5×</option><option value="1" selected>1×</option></select></label>
<span id="clock" class="clock">0.00 s</span></div>
<p class="muted">Ο εμφανιζόμενος χρόνος αντιστοιχεί στα αρχικά καρέ και συμφωνεί με τον χρόνο πάνω στο βίντεο. Δεν είναι επαληθευμένη ώρα του ρολογιού της κάμερας. Οι αποκομμένες κινήσεις στην αρχή ή στο τέλος σημειώνονται ως τέτοιες.</p>
<div class="form">
<label>Πλευρά (μόνο για διάκριση κινήσεων)<select id="position"><option value="left">Αριστερά</option><option value="right">Δεξιά</option><option value="both">Και οι δύο</option><option value="unknown">Δεν διακρίνεται</option></select></label>
<label>Πόσα ολόκληρα μπλοκ;<input id="quantity" type="number" min="0" step="1" placeholder="Κενό = δεν φαίνεται"></label>
<label>Σηκώνει στο (s)<input id="lift" type="number" step="0.01" min="0" placeholder="Κενό = πριν την αρχή"><button id="setLift">Σηκώνει τώρα</button></label>
<label>Αφήνει στο (s)<input id="release" type="number" step="0.01" min="0" placeholder="Κενό = μετά το τέλος"><button id="setRelease">Αφήνει τώρα</button></label>
<label>Τι κάνει;<select id="destination"><option value="filling_tank">Βάζει φέτα στη δεξαμενή</option><option value="scrap_tank">Πετάει τρίμμα</option><option value="no_deposit">Κίνηση χωρίς τοποθέτηση</option><option value="unknown">Δεν φαίνεται / αβέβαιο</option></select></label>
<label>Σχόλιο<input id="notes" placeholder="Π.χ. κρατά 2, τα αφήνει χωριστά"></label>
</div><div class="bar"><button id="add" class="primary">Προσθήκη σημείωσης</button><button id="clear">Καθαρισμός πεδίων</button></div><div id="message" class="message"></div>
<p class="note">Αν αφήνει τα κομμάτια χωριστά, μπορείς να γράψεις τους χρόνους στο σχόλιο. Αν δεν θέλεις να συμπληρώνεις τη φόρμα, στείλε στο chat: <b>C01 — 2 μπλοκ — σηκώνει 3,20 s — αφήνει 5,80 s — αριστερά</b>.</p>
<table><thead><tr><th>Κλιπ</th><th>Πλευρά</th><th>Μπλοκ</th><th>Σηκώνει</th><th>Αφήνει</th><th>Διάρκεια</th><th>Σχόλιο</th><th></th></tr></thead><tbody id="rows"></tbody></table>
<div class="bar"><button id="export" class="primary">Αποθήκευση απαντήσεων (JSON)</button><span class="muted">Οι σημειώσεις αποθηκεύονται σε αυτόν τον browser. Πάτησε αποθήκευση για να κρατήσεις αρχείο.</span></div>
<p id="summary" class="muted"></p></main><script>
const clips=__MANIFEST__;
const $=id=>document.getElementById(id), video=$('video');
const key='prolacata-expert-review-v4-20261027';
let notes=[];try{notes=JSON.parse(localStorage.getItem(key)||'[]')}catch(e){}
let current=clips[0];
for(const c of clips){const o=document.createElement('option');o.value=c.clip_id;o.textContent=c.clip_id+' — '+c.date+' — '+c.playback_duration_s.toFixed(1)+' s';$('clip').append(o)}
function frameIndex(){return Math.min(current.native_frame_count-1,Math.max(0,Math.floor(video.currentTime*current.playback_fps+1e-5)))}
function nativeTime(){return current.native_relative_timestamps_s[frameIndex()]}
function refreshClock(){$('clock').textContent=nativeTime().toFixed(2)+' s · καρέ '+frameIndex()}
function loadClip(){current=clips.find(c=>c.clip_id===$('clip').value);video.src=current.media_path;video.playbackRate=Number($('speed').value);$('source').textContent='Νέο παράδειγμα προς επιβεβαίωση · '+current.native_frame_count+' αρχικά καρέ';refreshClock()}
$('clip').onchange=loadClip;video.ontimeupdate=refreshClock;video.onseeked=refreshClock;
$('speed').onchange=()=>video.playbackRate=Number($('speed').value);
$('play').onclick=()=>video.paused?video.play():video.pause();
function step(delta){video.pause();video.currentTime=(Math.min(current.native_frame_count-1,Math.max(0,frameIndex()+delta))+.01)/current.playback_fps;refreshClock()}
$('prev').onclick=()=>step(-1);$('next').onclick=()=>step(1);
$('setLift').onclick=()=>{$('lift').value=nativeTime().toFixed(2)};
$('setRelease').onclick=()=>{$('release').value=nativeTime().toFixed(2)};
function clearFields(){for(const f of ['quantity','lift','release','notes'])$(f).value='';$('message').textContent=''}
$('clear').onclick=clearFields;
function value(id){return $(id).value===''?null:Number($(id).value)}
$('add').onclick=()=>{
 const q=value('quantity'),a=value('lift'),b=value('release');
 if(q!==null&&(!Number.isInteger(q)||q<0)){$('message').textContent='Η ποσότητα πρέπει να είναι ακέραιος ή κενή.';return}
 if(a!==null&&b!==null&&b<a){$('message').textContent='Ο χρόνος απόθεσης είναι πριν από τον χρόνο παραλαβής.';return}
 if([a,b].some(t=>t!==null&&(t<0||t>current.playback_duration_s))){$('message').textContent='Ο χρόνος βρίσκεται έξω από το απόσπασμα.';return}
 notes.push({clip_id:current.clip_id,source_sha256:current.source_sha256,position:$('position').value,quantity:q,lift_time_s:a,release_time_s:b,
 duration_s:a!==null&&b!==null?Number((b-a).toFixed(3)):null,destination:$('destination').value,notes:$('notes').value,
 timing_basis:'native clip-relative timestamp',pickup_left_censored:a===null,release_right_censored:b===null,
 annotation_origin:'browser review entry; verify against reviewer confirmation before training'});
 localStorage.setItem(key,JSON.stringify(notes));clearFields();render();$('message').textContent='Η σημείωση αποθηκεύτηκε τοπικά.';
};
const pos={left:'Αριστερά',right:'Δεξιά',both:'Και οι δύο',unknown:'Άγνωστο'};
function render(){const body=$('rows');body.replaceChildren();notes.forEach((n,i)=>{const tr=document.createElement('tr');
 for(const v of [n.clip_id,pos[n.position],n.quantity??'?',n.lift_time_s??'πριν',n.release_time_s??'μετά',n.duration_s??'?',n.destination+' · '+n.notes]){const td=document.createElement('td');td.textContent=v;tr.append(td)}
 const td=document.createElement('td'),b=document.createElement('button');b.textContent='Αφαίρεση';b.onclick=()=>{notes.splice(i,1);localStorage.setItem(key,JSON.stringify(notes));render()};td.append(b);tr.append(td);body.append(tr)});
 $('summary').textContent=notes.length+' σημειώσεις. Η απουσία σημείωσης δεν θεωρείται μηδενική τοποθέτηση.';
}
$('export').onclick=()=>{const out={schema_version:4,batch:'sequence_annotation_v4',events:notes,exhaustive_coverage_confirmed:false,eligible_for_training:false};
 const u=URL.createObjectURL(new Blob([JSON.stringify(out,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download='feta_review_v4_answers.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)};
loadClip();render();
</script></html>'''

def main():
    data=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'));assert len(data)==6
    payload=json.dumps(data,ensure_ascii=False).replace('</','<\\/')
    (OUT/'review.html').write_text(HTML.replace('__MANIFEST__',payload),encoding='utf-8')
    instructions='''ΠΡΩΤΗ ΠΑΡΤΙΔΑ: C01–C06, περίπου 30 δευτερόλεπτα το καθένα.

Άνοιξε το review.html στον browser. Τα βίντεο λειτουργούν και χωρίς σύνδεση στο Internet.
Χρησιμοποίησε ταχύτητα 0,5× ή 0,25× και τα κουμπιά «Καρέ».
Για κάθε μεταφορά σημείωσε ποσότητα, χρόνο που σηκώνεται και χρόνο που αφήνεται.
Η διάρκεια υπολογίζεται αυτόματα. Η πλευρά είναι μόνο για να ξεχωρίζουν ταυτόχρονες κινήσεις.
Δεν χρειάζονται στοιχεία ή ταυτότητα εργαζομένου.

Εναλλακτικά απάντησε στο chat:
C01 — αριστερά — 2 μπλοκ — σηκώνει 3,20 — αφήνει 5,80.
Οι αριθμοί του παραδείγματος είναι φανταστικοί, όχι επισήμανση του C01.

Αν δεν φαίνεται η ποσότητα, γράψε «δεν φαίνεται». Αν η κίνηση κόβεται, γράψε «ξεκίνησε πριν» ή «συνεχίζει μετά».
Αν δεν μπαίνει κανένα μπλοκ, πες το μαζί με τη σχετική κίνηση (τρίμμα, κενά χέρια, παλέτα).
Αν τα αφήνει χωριστά, σημείωσε τους επιμέρους χρόνους στο σχόλιο.
Στο τέλος κάθε αποσπάσματος δώσε και το συνολικό πλήθος που προστέθηκε κατά τη διάρκειά του.

Οι χρόνοι είναι σχετικοί με το απόσπασμα και προέρχονται από τα αρχικά καρέ.
Δεν αποτελούν επαληθευμένη ώρα κάμερας. Στην προεπισκόπηση τα καρέ προβάλλονται με σταθερό ρυθμό,
αλλά ο καμένος χρόνος και τα πεδία της φόρμας κρατούν τους αρχικούς μεταβλητούς χρόνους.
Δεν έχουν προστεθεί προβλέψεις μοντέλου ή υποτιθέμενες ποσότητες.
Και τα έξι είναι υποψήφια εκπαίδευσης. Η 26/9 και η 3/10 δεν χρησιμοποιούνται σε αυτή την παρτίδα.
'''
    (OUT/'ΟΔΗΓΙΕΣ.txt').write_text(instructions,encoding='utf-8')
    (OUT/'answer_template.txt').write_text('Για κάθε C01, C02, C03, C04, C05, C06:\nΣύνολο μπλοκ που μπήκαν: ...\nΠλευρά | Ποσότητα | Σηκώνει στο | Αφήνει στο | Παρατήρηση\n',encoding='utf-8')
    print(str(OUT/'review.html'))

if __name__=='__main__':main()
