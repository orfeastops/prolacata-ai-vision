"""Bookkeeping/causality tests; these do not measure visual counting accuracy."""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
import torch
from train_transfer_events_v4 import EventQuantityNet,decode,dataset,prepare_constraints,save,load

class TransferTests(unittest.TestCase):
    def test_temporary_windows_lock_preserves_valid_json(self):
        with tempfile.TemporaryDirectory() as folder:
            dest=Path(folder)/'progress.json';save(dest,{'epoch':1})
            original=Path.replace;calls=[]
            def locked_then_available(path,target):
                calls.append(1)
                if len(calls)<3:
                    self.assertEqual(load(dest),{'epoch':1})
                    raise PermissionError('simulated Windows sharing lock')
                return original(path,target)
            with patch.object(Path,'replace',locked_then_available):save(dest,{'epoch':2})
            self.assertEqual(load(dest),{'epoch':2})

    def test_temporal_head_is_causal(self):
        torch.manual_seed(11);model=EventQuantityNet(11).eval();x=torch.randn(1,11,150)
        with torch.no_grad():
            a=model(x);b=model(x[:,:,:90])
        torch.testing.assert_close(a[:,:,:,:90],b,atol=1e-6,rtol=1e-5)

    def fixture(self):
        t=np.arange(0,4,.1);phase=np.zeros((len(t),2,2),np.float32)
        q=np.zeros((len(t),2,3),np.float32);q[:,:,1]=1
        phase[5:13,0,0]=.9;phase[14:18,0,1]=.9
        return t,phase,q

    def test_one_episode_is_two_not_two_per_frame(self):
        a,u=decode(*self.fixture());self.assertEqual(len(a),1);self.assertFalse(u)
        self.assertEqual(a[0]['predicted_quantity'],2)
        self.assertGreater(a[0]['emitted_at_s'],a[0]['time_s'])

    def test_no_carry_support_cannot_be_counted(self):
        t,p,q=self.fixture();p[:,:,0]=0
        a,u=decode(t,p,q);self.assertFalse(a);self.assertEqual(len(u),1)

    def test_ambiguous_quantity_stays_unknown(self):
        t,p,q=self.fixture();q[:]=1/3
        a,u=decode(t,p,q);self.assertFalse(a);self.assertIn('quantity_ambiguous',u[0]['reasons'])

    def test_unfinished_release_not_finalized(self):
        t,p,q=self.fixture();p[14:,0,1]=.9
        a,u=decode(t,p,q);self.assertFalse(a);self.assertIn('release_episode_cut_off',u[0]['reasons'])

    def test_supervision_masks_and_split(self):
        rows=dataset();tr=[i for i,r in enumerate(rows) if r['role']=='train']
        self.assertEqual({rows[i]['id'] for i in tr},{'C01','C03','C04','C05','C06'})
        self.assertFalse({rows[i]['source_sha256'] for i in tr}&{r['source_sha256'] for r in rows if r['role']!='train'})
        events,neg=prepare_constraints(rows,tr,572)
        self.assertEqual(sum(len(rows[i]['masks']) for i in tr),2)
        c01=rows[0];split=[e for e in c01['events'] if e['parent']=='C01_U04']
        self.assertEqual([e['quantity'] for e in split],[1,1])
        self.assertEqual([e['carry_quantity'] for e in split],[2,1])
        self.assertTrue(all(e['release_interval'][0]>c01['original_end_s'] for e in split))
        c02=rows[1];self.assertFalse(any(e['quantity']==18 for e in c02['events']))
        self.assertTrue(any(m['reason']=='conflict_or_censored' for m in c02['masks']))
        self.assertGreater(len(events),0);self.assertGreater(len(neg),0)

if __name__=='__main__':
    torch.set_num_threads(4)
    unittest.main()
