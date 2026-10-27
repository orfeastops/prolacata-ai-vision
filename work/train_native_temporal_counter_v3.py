"""Source-held-out diagnostic of interval-supervised, causal count density.

Every cached original frame is used. Rates are experimental expected counts,
not verified object identities, releases, or a production-ready tank counter.
"""
import os
os.environ['YOLO_AUTOINSTALL'] = 'false'
import argparse
import hashlib
import json
import math
import time
from pathlib import Path

import cv2
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/facility_dataset/temporal_pipeline/placement_counter_v3'
OUT = BASE / 'native_temporal_diagnostic'
CONFIG = dict(
    seed=2701, projection_dim=256, channels=64, dilations=[1, 2, 4, 8, 16],
    epochs=400, learning_rate=.003, weight_decay=.01, dropout=.15,
    interval_margin_s=.125, pools=[[4, 8], [2, 4], [1, 2]],
    encoder='frozen generic yolo26n; no facility fine-tuning',
    input='projected spatial features, backward differences, absolute differences, previous native dt',
    output='two nonnegative count rates for spatial annotation positions; sum for total',
    temporal_sampling='every native decoded frame; no temporal resampling',
    supervision='clip position totals and count integrals within approximate release intervals',
    no_uniform_per_frame_count_targets=True,
    validation='leave one original source file out, including overlapping segments',
    no_hyperparameter_search=True, production_ready=False,
)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save_json(path, obj):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)


def integration_weights(times, start, stop):
    """Elapsed-time weights; the first sample also represents the prefix gap.

    The next timestamp closes an elapsed interval, with no future image input.
    No fabricated frames or nominal fps assumptions are used.
    """
    t = np.asarray(times, dtype=np.float64)
    if not (len(t) > 0 and np.all(np.diff(t) > 0) and start <= t[0] < t[-1] < stop):
        raise ValueError('Invalid native timestamps or interval')
    dt = np.diff(np.r_[t, stop])
    dt[0] += t[0] - start
    assert np.all(dt > 0) and np.isclose(dt.sum(), stop - start)
    return dt.astype(np.float32)


def expand_features(z, times):
    delta = np.zeros_like(z)
    delta[1:] = z[1:] - z[:-1]
    dt = np.r_[1 / 15, np.diff(times)].astype(np.float32)[:, None]
    return np.concatenate([z, delta, np.abs(delta), dt], axis=1)


class CausalResidual(nn.Module):
    def __init__(self, channels, dilation, dropout):
        super().__init__()
        self.padding = 2 * dilation
        self.conv = nn.Conv1d(channels, channels, 3, dilation=dilation)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        return x + self.dropout(F.gelu(self.conv(F.pad(x, (self.padding, 0)))))


class TemporalCounter(nn.Module):
    def __init__(self, input_dim, config=CONFIG):
        super().__init__()
        self.project = nn.Conv1d(input_dim, config['channels'], 1)
        self.layers = nn.Sequential(*[
            CausalResidual(config['channels'], d, config['dropout'])
            for d in config['dilations']])
        self.head = nn.Conv1d(config['channels'], 2, 1)
        nn.init.normal_(self.head.weight, std=.005)
        nn.init.constant_(self.head.bias, -3.)

    def forward(self, x):
        return F.softplus(self.head(self.layers(F.gelu(self.project(x)))))


def extract_features(rows, encoder_path):
    from ultralytics import YOLO
    encoder_sha = digest(encoder_path)
    feature_dir = OUT / 'features'
    feature_dir.mkdir(exist_ok=True)
    encoder = YOLO(str(encoder_path)).model.eval()
    for p in encoder.parameters():
        p.requires_grad = False
    captured = []

    def hook(_module, args):
        captured.clear()
        assert len(args[0]) == len(CONFIG['pools'])
        captured.extend(F.adaptive_avg_pool2d(x, tuple(pool)).flatten(1)
                        for x, pool in zip(args[0], CONFIG['pools']))

    handle = encoder.model[-1].register_forward_pre_hook(hook)
    projection_path = OUT / 'fixed_projection.npy'
    projection = torch.from_numpy(np.load(projection_path)) if projection_path.exists() else None
    arrays, times_list, weights = [], [], []
    for i, row in enumerate(rows):
        path = BASE / 'native_frames' / (row['segment_id'] + '.npz')
        cache = feature_dir / path.name
        native_sha = digest(path)
        with np.load(path) as data:
            times = data['timestamps'].copy()
            ids = data['source_frame_indices']
            assert np.all(np.diff(ids) == 1)
            assert str(data['source_sha256']) == row['source_sha256']
            if cache.exists():
                with np.load(cache) as prior:
                    assert str(prior['native_cache_sha256']) == native_sha
                    assert str(prior['encoder_sha256']) == encoder_sha
                    z = prior['features'].copy()
            else:
                frames = data['frames']
                zz = []
                for start in range(0, len(frames), 8):
                    batch = [cv2.copyMakeBorder(cv2.cvtColor(f, cv2.COLOR_BGR2RGB),
                             12, 12, 0, 0, cv2.BORDER_CONSTANT, value=(114, 114, 114))
                             for f in frames[start:start+8]]
                    x = torch.from_numpy(np.stack(batch)).permute(0, 3, 1, 2).float() / 255
                    with torch.inference_mode():
                        encoder(x)
                        features = torch.cat(captured, dim=1)
                        if projection is None:
                            generator = torch.Generator().manual_seed(CONFIG['seed'])
                            projection = torch.randn(features.shape[1], CONFIG['projection_dim'],
                                generator=generator) / math.sqrt(features.shape[1])
                            np.save(projection_path, projection.numpy())
                        zz.append((features @ projection).numpy())
                z = np.concatenate(zz).astype(np.float32)
                np.savez_compressed(cache, features=z, timestamps=times,
                    native_cache_sha256=native_sha, encoder_sha256=encoder_sha)
        assert len(z) == len(times)
        start, stop = row['source_encoded_interval_s']
        arrays.append(torch.from_numpy(expand_features(z, times)))
        times_list.append(times - start)
        weights.append(torch.from_numpy(integration_weights(times, start, stop)))
        save_json(OUT / 'progress.json', dict(stage='native_frame_features',
            completed=i+1, total=len(rows), processed_frames=sum(len(x) for x in arrays)))
        print(f'Native features {i+1}/{len(rows)}: {row["segment_id"]}, {len(z)} frames', flush=True)
    handle.remove()
    del encoder
    return arrays, times_list, weights, encoder_sha


def training_batch(rows, arrays, times, weights, indices, mean, scale):
    max_len = max(len(arrays[i]) for i in indices)
    dim = arrays[0].shape[1]
    x = torch.zeros(len(indices), dim, max_len)
    w = torch.zeros(len(indices), max_len)
    allowed = torch.zeros(len(indices), 2, max_len, dtype=torch.bool)
    targets = torch.tensor([rows[i]['position_totals'] for i in indices], dtype=torch.float32)
    events = []
    for j, i in enumerate(indices):
        n = len(arrays[i])
        x[j, :, :n] = ((arrays[i] - mean) / scale).T
        w[j, :n] = weights[i]
        for event in rows[i]['events']:
            pos = ['left', 'right'].index(event['position'])
            a, b = event['release_interval_s']
            mask = torch.zeros(max_len)
            mask[:n] = torch.from_numpy(((times[i] >= a-CONFIG['interval_margin_s']) &
                (times[i] <= b+CONFIG['interval_margin_s'])).astype(np.float32))
            assert mask.sum() > 0
            allowed[j, pos] |= mask.bool()
            if event['quantity'] is not None:
                events.append((j, pos, mask, float(event['quantity'])))
    return x, w, allowed, targets, events


def fit(rows, arrays, times, weights, indices):
    torch.manual_seed(CONFIG['seed'])
    joined = torch.cat([arrays[i] for i in indices])
    mean = joined.mean(0)
    scale = joined.std(0).clamp_min(.05)
    x, w, allowed, targets, events = training_batch(rows, arrays, times, weights, indices, mean, scale)
    model = TemporalCounter(x.shape[1])
    optimizer = torch.optim.AdamW(model.parameters(), lr=CONFIG['learning_rate'],
                                  weight_decay=CONFIG['weight_decay'])
    losses = []
    for epoch in range(CONFIG['epochs']):
        model.train()
        optimizer.zero_grad()
        increments = model(x) * w[:, None, :]
        totals = increments.sum(2)
        total_loss = ((totals-targets).square() / (1+targets)).mean()
        interval_loss = torch.stack([
            ((increments[j, pos]*mask).sum()-q).square()/(1+q)
            for j, pos, mask, q in events]).mean()
        outside = (increments * ~allowed).sum(2)
        outside_loss = outside.square().mean()
        loss = total_loss + interval_loss + outside_loss
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 5.)
        optimizer.step()
        if epoch % 50 == 0 or epoch == CONFIG['epochs']-1:
            losses.append(dict(epoch=epoch+1,loss=float(loss.detach()),
                total_loss=float(total_loss.detach()),interval_loss=float(interval_loss.detach()),
                outside_loss=float(outside_loss.detach())))
    return model.eval(), mean, scale, losses


def predict(model, mean, scale, array, weights):
    with torch.inference_mode():
        rate = model(((array-mean)/scale).T[None])[0].T
    increments = rate * weights[:, None]
    return rate.numpy(), increments.numpy()


def run():
    torch.set_num_threads(4)
    cv2.setNumThreads(2)
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / 'results.json').exists():
        raise RuntimeError('Completed frozen diagnostic exists; do not overwrite or tune on its folds')
    labels_path = BASE / 'interval_supervision.json'
    labels = json.loads(labels_path.read_text(encoding='utf-8'))
    rows = labels['segments']
    assert all(r['date'] in ('2026-10-01', '2026-10-21') for r in rows)
    assert json.loads((BASE / 'native_alignment_audit.json').read_text())['all_passed']
    if (OUT / 'config.json').exists():
        assert json.loads((OUT / 'config.json').read_text()) == CONFIG
    else:
        save_json(OUT / 'config.json', CONFIG)
    encoder_path = ROOT / 'outputs/feta_training/yolo26n.pt'
    started = time.time()
    arrays, times, weights, encoder_sha = extract_features(rows, encoder_path)
    sources = sorted({r['source_sha256'] for r in rows})
    predictions, fold_logs = [], []
    for fold, source in enumerate(sources):
        train = [i for i,r in enumerate(rows) if r['source_sha256'] != source]
        test = [i for i,r in enumerate(rows) if r['source_sha256'] == source]
        assert not {rows[i]['source_sha256'] for i in train} & {rows[i]['source_sha256'] for i in test}
        model, mean, scale, losses = fit(rows, arrays, times, weights, train)
        fold_path = OUT / f'fold_{fold+1:02d}.pt'
        torch.save(dict(model=model.state_dict(), mean=mean, scale=scale,
            config=CONFIG, train_sources=sorted({rows[i]['source_sha256'] for i in train}),
            excluded_source=source, labels_sha256=digest(labels_path),
            encoder_sha256=encoder_sha), fold_path)
        for i in test:
            rate, inc = predict(model, mean, scale, arrays[i], weights[i])
            total = float(inc.sum())
            pred = dict(segment_id=rows[i]['segment_id'], source_sha256=source,
                confirmed_count=rows[i]['confirmed_count'], expected_count=total,
                rounded_count=int(math.floor(total+.5)),
                expected_counts_by_position=inc.sum(0).tolist(),
                reference_counts_by_position=rows[i]['position_totals'],
                absolute_error=abs(total-rows[i]['confirmed_count']),
                fold_checkpoint=fold_path.name,
                role='source-held-out development prediction, not an untouched independent test')
            predictions.append(pred)
            np.savez_compressed(OUT / (rows[i]['segment_id']+'_held_out.npz'),
                native_relative_times=times[i], rates=rate, increments=inc,
                confirmed_count=rows[i]['confirmed_count'], excluded_source=source)
        fold_logs.append(dict(fold=fold+1, excluded_source=source, training_losses=losses))
        save_json(OUT / 'progress.json', dict(stage='source_cross_validation',
            completed=fold+1,total=len(sources),elapsed_s=time.time()-started))
        print(f'Source-held-out training {fold+1}/{len(sources)} complete', flush=True)
    mae = float(np.mean([p['absolute_error'] for p in predictions]))
    positives = [p for p in predictions if p['confirmed_count'] > 0]
    negatives = [p for p in predictions if p['confirmed_count'] == 0]
    model, mean, scale, losses = fit(rows, arrays, times, weights, list(range(len(rows))))
    torch.save(dict(model=model.state_dict(),mean=mean,scale=scale,config=CONFIG,
        train_sources=sources,encoder_sha256=encoder_sha,labels_sha256=digest(labels_path)),
        OUT / 'experimental_native_temporal_counter.pt')
    fit_counts = []
    for i in range(len(rows)):
        _, inc = predict(model,mean,scale,arrays[i],weights[i])
        fit_counts.append(dict(segment_id=rows[i]['segment_id'], expected_count=float(inc.sum()),
            reference_count=rows[i]['confirmed_count'], scope='training fit only'))
    report = dict(config=CONFIG, training_performed=True,
        labels_sha256=digest(labels_path), encoder_sha256=encoder_sha,
        native_frames=sum(len(a) for a in arrays), deliberately_skipped_frames=0,
        source_files=len(sources), segments=len(rows), confirmed_blocks=sum(r['confirmed_count'] for r in rows),
        source_held_out_mae=mae,
        source_held_out_rounded_exact=sum(p['rounded_count']==p['confirmed_count'] for p in predictions),
        positive_clips_rounded_exact=sum(p['rounded_count']==p['confirmed_count'] for p in positives),
        positive_clips=len(positives),negative_clips_false_positive=sum(p['rounded_count']>0 for p in negatives),
        negative_clips=len(negatives),predictions=predictions,training_fit=fit_counts,
        training_loss_logs=fold_logs+[dict(fold='all_sources',training_losses=losses)],
        elapsed_seconds=time.time()-started, production_ready=False,
        release_precision=None,release_recall=None,tank_count=None,
        september_used=False, october3_used=False,
        limitations=[
            'Only 12 short reviewed segments, seven positive, from 10 original source files.',
            'Release intervals were reviewed by assistant; exact timestamps are not user-verified.',
            'An interval count-rate regressor is not an individually verified block detector or tracker.',
            'Source folds are development checks already used by previous approaches, not fresh test data.',
            'Final checkpoint uses all reviewed October sources; displayed validation uses excluded-source checkpoints.',
            'No automatic tank changes, cross-camera association or live acceptance evaluation.',
            'No attribution of any change exclusively to fps: supervision and architecture changed as well.'
        ])
    save_json(OUT / 'results.json', report)
    save_json(OUT / 'progress.json', dict(stage='complete',training_performed=True,
        elapsed_s=time.time()-started,production_ready=False))
    print(json.dumps({k:report[k] for k in ('native_frames','source_held_out_mae',
        'positive_clips_rounded_exact','positive_clips','negative_clips_false_positive',
        'negative_clips','elapsed_seconds','production_ready')}),flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.parse_args()
    run()
