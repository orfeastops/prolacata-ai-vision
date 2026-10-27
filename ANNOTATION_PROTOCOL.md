# Annotation protocol for completed block transfers

## Reviewer input

For each transfer, capture:

| Field | Meaning |
|---|---|
| Clip ID | C01–C06 for the current batch |
| Position | Left, right, both or unknown; a spatial distinction, not identity |
| Quantity | Actual whole blocks carried/deposited; blank if not visible |
| Lift time | When the cheese leaves the tray/conveyor |
| Release time | When the cheese is left inside the destination tank |
| Destination/action | Filling tank, scrap/crumb tank, no deposit, or uncertain |
| Notes | Separate releases, occlusion, ambiguous quantity or boundary conditions |
| Clip total | All whole blocks added during the clip, independently checked |

Carry duration is calculated from the two timestamps; do not make the reviewer calculate it separately. If two/three blocks are released at different moments, preserve the sub-release times in notes or separate linked release records. The total must remain the actual number of physical blocks.

If a pickup began before the clip or release happens after the clip, mark it as boundary-censored. A partial movement is not evidence for zero quantity. Ask for additional context only when it is needed to resolve a specific ambiguity.

## Assistant annotation work

The user's quantities and event timing must be linked to the actual visible cheese in the source frames. Prepare object or carried-group boxes/masks at pickup, during transport and at release. Track the same physical object/group through the sequence. Gloves touching a tray are not sufficient evidence that a block was lifted.

The current v4 files are review candidates, not a finished supervised object-tracking dataset. `expert_review_complete`, exhaustive coverage and training eligibility remain false until the feedback is checked. Do not present these templates as completed labels.

Preserve the distinction between:

- expert-confirmed quantities and semantic corrections;
- assistant-reviewed approximate intervals;
- inferred model boxes/track associations;
- unknown or occluded evidence.

The previous v3 interval dataset had only one known three-block release and two quantity-unknown releases with a confirmed combined total. Do not arbitrarily assign the unknown pair to three plus two. New explicit examples should improve this coverage without assuming that more labels alone guarantee success.

## Counting and evaluation

Use completed releases into the intended filling tank as count evidence. Retain uncertainty when quantity, destination or association is unresolved. Keep crumb disposal, salt handling, empty gestures, separators and moving empty trays as relevant negative/confusable cases. Do not report all hand trajectories as blocks.

Split by original source/event group; overlapping clips and extracted frames from a source must remain in one split. Record source hashes, frame indexes, timestamps, checkpoint hashes and the exact algorithm/configuration used. Freeze predictions before comparing with new expert totals.

Evaluate both positive counts and false counts on negative intervals. Report absolute count error and exact totals separately from event precision/recall; only report event precision/recall when sufficiently complete event ground truth exists. A rounded clip estimate matching the total can still contain cancelling misses and false positives.

October 1/21 are development/annotation sources for this batch. Keep October 3 reserved and September 26 excluded from training. September 26 has already been inspected for failures, so future final acceptance should use additional untouched production footage with independently recorded truth.
