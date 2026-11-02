"""Build a local, prediction-blind human event review page from the hour plan."""
import json
from pathlib import Path

BASE = Path('D:/Codex/tank-storage')
plan = json.loads((BASE / 'one_hour_plan.json').read_text(encoding='utf-8'))
clips = [{ 'id': f"clip_{f['index']:03d}", 'src': ((BASE/'review_proxies'/f"clip_{f['index']:03d}.mp4") if (BASE/'review_proxies'/f"clip_{f['index']:03d}.mp4").exists() else Path(f['source'])).as_uri(),
           'start': f['filename_start'][-6:], 'end': f['filename_end'][-6:] }
         for f in plan['files']]
template = r'''<!doctype html><html lang="el"><meta charset="utf-8">
<title>Δωμάτιο 11 — έλεγχος μίας ώρας</title>
<style>body{font:18px system-ui;max-width:1150px;margin:24px auto;padding:0 20px;background:#101827;color:#eef3fb}button,select,input,textarea{font:inherit;padding:8px;margin:4px;border-radius:6px}button{cursor:pointer}video{width:100%;max-height:550px;background:black}section{background:#202c40;padding:18px;margin:16px 0;border-radius:12px}label{display:block;margin:10px 0}small{color:#b7c8de}table{width:100%;border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #53627a;text-align:left}.warn{color:#ffce80}textarea{width:90%}a{color:#8bd7ff}</style>
<h1>Μία ώρα — αποθηκεύσεις δωματίου 11</h1>
<p>28/10/2026, ζητούμενο διάστημα <b>09:15–10:15</b>. Μετράμε μία φορά όταν οι εργαζόμενοι βάλουν τυρί στη δεξαμενή και η ίδια βγει. Η ώρα καταγράφεται από το ρολόι της κάμερας.</p>
<p>Δες τα βίντεο με τη σειρά. Υπάρχει υλικό πριν/μετά την ώρα για να φαίνεται η συνέχεια. Κατάγραψε και αβεβαιότητες ή κενά. Οι χρόνοι των ονομάτων αρχείων δεν εγγυώνται συνεχή κάλυψη. Δεν εμφανίζονται προβλέψεις μοντέλου.</p>
<section><label>Απόσπασμα <select id="clip"></select></label><div id="range"></div>
<video id="video" controls preload="metadata"></video><p id="videoError" class="warn"></p>
<button id="back">−5 δευτ.</button><button id="forward">+5 δευτ.</button>
<select id="speed"><option value="1">1×</option><option value="1.5">1,5×</option><option value="2">2×</option><option value="3">3×</option></select>
<button id="markFill">Σημείο τοποθέτησης τυριού</button><span id="fillLabel">Δεν σημειώθηκε ακόμη</span>
<p><small>Το σημείο τοποθέτησης μπορεί να είναι στο προηγούμενο αρχείο. Η αλλαγή αρχείου το διατηρεί μέχρι να καταχωρίσεις το συμβάν.</small></p>
<label>Στο σημείο εξόδου, ώρα κάμερας <input id="clock" type="time" step="1" required></label>
<label>Τι παρατήρησες; <select id="kind"><option value="">Επίλεξε…</option><option value="storage">Τυρί → ίδια δεξαμενή → έξοδος</option><option value="uncertain">Αβέβαιη συνέχεια / δεν φάνηκε το γέμισμα</option><option value="not_storage">Έξοδος χωρίς την παραπάνω διαδικασία</option><option value="duplicate">Επανάληψη συμβάντος από άλλο αρχείο</option></select></label>
<label>Σχόλιο / σύνδεση με προηγούμενο συμβάν <textarea id="note" rows="2"></textarea></label>
<button id="add">Καταχώριση στο τωρινό σημείο βίντεο</button><p id="feedback"></p>
<label>Έλεγχος αυτού του αποσπάσματος <select id="coverage"><option value="unreviewed">Δεν ελέγχθηκε</option><option value="partial">Ελέγχθηκε εν μέρει</option><option value="complete_events">Ελέγχθηκε ολόκληρο — καταγράφηκαν συμβάντα</option><option value="complete_zero">Ελέγχθηκε ολόκληρο — καμία αποθήκευση</option></select></label>
<label>Κενά, εμπόδια στην εικόνα ή επαναλαμβανόμενα σημεία <textarea id="gaps" rows="2"></textarea></label></section>
<section><h2>Οι σημειώσεις σου</h2><p id="counts"></p><table><thead><tr><th>Αρχείο</th><th>Ώρα</th><th>Παρατήρηση</th><th></th></tr></thead><tbody id="rows"></tbody></table>
<button id="download">Λήψη απαντήσεων JSON</button><label>Επαναφορά απαντήσεων <input id="import" type="file" accept="application/json,.json"></label>
<p id="saveState"></p><p><b>Όταν τελειώσεις, πάτησε «Λήψη απαντήσεων JSON» και δώσε το αρχείο στη συνομιλία.</b> Η σελίδα κρατά προσωρινά τις σημειώσεις στον ίδιο browser· δεν ενημερώνει αυτόματα την αξιολόγηση.</p></section>
<script>
const clips=__CLIPS__, $=id=>document.getElementById(id), key='room11-hour-manual-v1';
let state={schema:'room11-hour-manual-v1',date:'2026-10-28',window:['09:15:00','10:15:00'],events:[],coverage:{}}, fill=null;
try{const s=JSON.parse(localStorage.getItem(key));if(s&&s.schema===state.schema&&Array.isArray(s.events)&&s.coverage)state=s}catch(e){}
const names={storage:'Τοποθέτηση και έξοδος',uncertain:'Αβέβαιο',not_storage:'Άλλη έξοδος',duplicate:'Επανάληψη'};
function save(){state.updated_at=new Date().toISOString();try{localStorage.setItem(key,JSON.stringify(state));$('saveState').textContent='Προσωρινά αποθηκευμένο στον browser. Κατέβασε JSON για μόνιμο αντίγραφο.'}catch(e){$('saveState').textContent='Η προσωρινή αποθήκευση δεν είναι διαθέσιμη. Κατέβασε JSON πριν κλείσεις.'}render()}
function render(){const rows=$('rows');rows.replaceChildren();for(const e of state.events){const tr=document.createElement('tr');for(const s of [e.exit.clip,e.camera_time,names[e.kind]]){const td=document.createElement('td');td.textContent=s;tr.append(td)}const td=document.createElement('td'),b=document.createElement('button');b.textContent='Διαγραφή';b.onclick=()=>{if(confirm('Διαγραφή αυτής της σημείωσης;')){state.events=state.events.filter(x=>x.id!==e.id);save()}};td.append(b);tr.append(td);rows.append(tr)}const n=Object.values(state.coverage).filter(x=>x.status.startsWith('complete')).length;$('counts').textContent=`${state.events.length} σημειώσεις · ${n}/${clips.length} αρχεία δηλώθηκαν πλήρως ελεγμένα. Οι σημειώσεις δεν έχουν ακόμη συμφιλιωθεί ως προς επικαλύψεις.`}
for(const c of clips){const o=document.createElement('option');o.value=c.id;o.textContent=c.id;$('clip').append(o)}
function loadClip(){const c=clips.find(x=>x.id===$('clip').value);$('video').src=c.src;$('range').textContent=`Όνομα αρχείου: ${c.start}–${c.end} (έλεγξε το ορατό ρολόι)`;$('videoError').textContent='';const v=state.coverage[c.id]||{};$('coverage').value=v.status||'unreviewed';$('gaps').value=v.notes||''}
$('video').onerror=()=>{$('videoError').textContent='Το βίντεο δεν άνοιξε σε αυτόν τον browser. Άνοιξε το HTML τοπικά σε Edge ή Chrome. Μην δηλώσεις έλεγχο αν δεν είδες το βίντεο.'};
$('clip').onchange=loadClip;$('back').onclick=()=>{$('video').currentTime=Math.max(0,$('video').currentTime-5)};$('forward').onclick=()=>{$('video').currentTime=Math.min($('video').duration,$('video').currentTime+5)};$('speed').onchange=()=>{$('video').playbackRate=Number($('speed').value)};
$('markFill').onclick=()=>{fill={clip:$('clip').value,video_seconds:$('video').currentTime};$('fillLabel').textContent=`${fill.clip}, ${fill.video_seconds.toFixed(1)} s`};
$('add').onclick=()=>{const kind=$('kind').value, time=$('clock').value;if(!kind||!time){$('feedback').textContent='Συμπλήρωσε ώρα κάμερας και παρατήρηση.';return}if(kind==='storage'&&!fill){$('feedback').textContent='Σημείωσε πρώτα πού είδες την τοποθέτηση τυριού, ή επίλεξε αβέβαιη συνέχεια.';return}state.events.push({id:Date.now().toString()+'-'+Math.random().toString(36).slice(2),kind,camera_time:time.length===5?time+':00':time,placement:fill,exit:{clip:$('clip').value,video_seconds:$('video').currentTime},notes:$('note').value});fill=null;$('fillLabel').textContent='Δεν σημειώθηκε ακόμη';$('note').value='';$('clock').value='';$('kind').value='';$('feedback').textContent='Καταχωρίστηκε.';save()};
function coverage(){state.coverage[$('clip').value]={status:$('coverage').value,notes:$('gaps').value};save()}$('coverage').onchange=coverage;$('gaps').onchange=coverage;
$('download').onclick=()=>{save();const a=document.createElement('a'),url=URL.createObjectURL(new Blob([JSON.stringify(state,null,2)],{type:'application/json'}));a.href=url;a.download='room11_2026-10-28_manual_review.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
$('import').onchange=async e=>{try{const s=JSON.parse(await e.target.files[0].text());if(s.schema!==state.schema||!Array.isArray(s.events)||!s.coverage||s.events.some(x=>!x.exit||!names[x.kind]))throw Error('Μη συμβατό αρχείο');if(confirm('Αντικατάσταση των τωρινών σημειώσεων με το αρχείο;')){state=s;save();loadClip()}}catch(err){alert('Δεν έγινε εισαγωγή: '+err.message)}};
loadClip();render();
</script></html>'''
template = template.replace('<label>Στο σημείο εξόδου, ώρα κάμερας', '<button id="fillOnly">Μόνο γέμισμα — δεν παρατηρήθηκε έξοδος</button><p><small>Για μόνο γέμισμα, πάτησε αυτό το κουμπί στο σημείο που το βλέπεις. Δεν απαιτείται ώρα εξόδου και δεν προσμετράται ως αποθήκευση.</small></p><label>Μόνο εφόσον παρατηρήθηκε έξοδος: ώρα κάμερας')
template = template.replace("const names={storage:", "const names={filling_only:'Μόνο γέμισμα — χωρίς παρατηρημένη έξοδο',storage:")
template = template.replace('e.exit.clip,e.camera_time,names[e.kind]', "(e.exit||e.placement).clip,e.camera_time||'—',names[e.kind]")
template = template.replace("x=>!x.exit||!names[x.kind]", "x=>!(x.exit||x.placement)||!names[x.kind]")
template = template.replace('loadClip();render();', '''$('fillOnly').onclick=()=>{const pos={clip:$('clip').value,video_seconds:$('video').currentTime};fill=pos;state.events.push({id:Date.now().toString()+'-'+Math.random().toString(36).slice(2),kind:'filling_only',camera_time:null,placement:pos,exit:null,notes:$('note').value});$('fillLabel').textContent=`${pos.clip}, ${pos.video_seconds.toFixed(1)} s`;$('feedback').textContent='Αποθηκεύτηκε μόνο το γέμισμα. Δεν μετρήθηκε αποθήκευση. Το σημείο διατηρείται για πιθανή μεταγενέστερη έξοδο.';$('note').value='';save()};
loadClip();render();''')
out = BASE / 'hour_manual_review.html'
out.write_text(template.replace('__CLIPS__', json.dumps(clips, ensure_ascii=False)), encoding='utf-8')
assert all(Path(f['source']).is_file() for f in plan['files'])
cpath = BASE / 'continuation.json'
c = json.loads(cpath.read_text(encoding='utf-8'))
c['human_review_page'] = str(out)
c.setdefault('human_review_status', 'page_prepared_no_user_annotations_received')
c['human_review_form_supports_filling_only'] = True
cpath.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'page':str(out),'source_links_verified':len(clips),'new_manual_labels':0}))
