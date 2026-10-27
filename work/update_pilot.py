from pathlib import Path
p=Path('outputs/feta_pilot/review.html')
s=p.read_text(encoding='utf-8')
s=s.replace("return:'Επιστροφή / χωρίς τοποθέτηση'", "return:'Επιστροφή / χωρίς τοποθέτηση',separator:'Διαχωριστικό / άλλο αντικείμενο'")
s=s.replace("['crumb','return'].includes(x.destination)", "['crumb','return','separator'].includes(x.destination)")
p.write_text(s,encoding='utf-8')
p=Path('outputs/feta_pilot/count_events.py')
s=p.read_text(encoding='utf-8').replace("('crumb', 'return')", "('crumb', 'return', 'separator')")
p.write_text(s,encoding='utf-8')
