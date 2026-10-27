"""Check temporal leakage and timestamp integration, not model accuracy."""
import unittest
import numpy as np
import torch
from train_native_temporal_counter_v3 import TemporalCounter, integration_weights, expand_features, training_batch


class NativeTemporalTests(unittest.TestCase):
    def test_future_images_cannot_change_past_predictions(self):
        torch.manual_seed(5)
        model=TemporalCounter(7).eval()
        x=torch.randn(2,7,100)
        changed=x.clone();changed[:,:,50:]=torch.randn(2,7,50)*100
        with torch.inference_mode():
            a=model(x);b=model(changed)
        torch.testing.assert_close(a[:,:,:50],b[:,:,:50],rtol=0,atol=0)

    def test_causal_feature_differences(self):
        x=np.arange(30,dtype=np.float32).reshape(10,3)
        modified=x.copy();modified[5:]=1000
        times=np.arange(10)/15
        np.testing.assert_array_equal(expand_features(x,times)[:5],expand_features(modified,times)[:5])

    def test_variable_dt_covers_interval_once(self):
        times=np.array([.02,.06,.14,.18,.30])
        weights=integration_weights(times,0,.4)
        np.testing.assert_allclose(weights,[.06,.08,.04,.12,.10],atol=1e-6)
        self.assertAlmostEqual(float(weights.sum()),.4,places=6)
        self.assertAlmostEqual(float((weights*3).sum()),1.2,places=6)

    def test_duplicate_timestamps_rejected(self):
        with self.assertRaises(ValueError):
            integration_weights([0,.04,.04],0,.1)

    def test_unknown_event_quantity_is_not_guessed(self):
        rows=[dict(position_totals=[5,0],events=[
            dict(position='left',release_interval_s=[.2,.4],quantity=None),
            dict(position='left',release_interval_s=[.6,.8],quantity=None)])]
        arrays=[torch.ones(15,3)]
        times=[np.arange(15)/15]
        weights=[torch.ones(15)/15]
        _,_,allowed,targets,events=training_batch(rows,arrays,times,weights,[0],
            torch.zeros(3),torch.ones(3))
        self.assertEqual(events,[])
        self.assertEqual(targets.tolist(),[[5,0]])
        self.assertTrue(allowed[0,0].any())
        self.assertFalse(allowed[0,1].any())

    def test_right_padding_cannot_change_real_frames(self):
        torch.manual_seed(7)
        model=TemporalCounter(7).eval()
        x=torch.randn(1,7,45)
        padded=torch.nn.functional.pad(x,(0,55))
        with torch.inference_mode():
            a=model(x);b=model(padded)
        torch.testing.assert_close(a,b[:,:,:45],atol=1e-6,rtol=1e-5)


if __name__=='__main__':
    torch.set_num_threads(2)
    unittest.main()
