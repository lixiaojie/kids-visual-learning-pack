# Cross Renderer Decisions

> Date: 2026-05-14
> Scope: Yutou Verse EdgeOne H5 + Taro WeChat Mini Program

## 1. Representative Objects On Mini Program

Decision: keep `representativeObjects` fully expanded and static in the mini program.

Reasoning: on mobile, vertical reading is natural and lower-friction than forcing children or parents to tap each object to reveal the explanation. This differs from the EdgeOne H5 interaction, where object cards can be selected and expanded, but it does not remove educational content.

Renderer expectation:

- EdgeOne H5: object card selection may reveal detail and drive related group highlighting.
- Mini Program: object name and `childExplanation` render directly for every object.

This is an intentional simplification, not a parity bug.

## 2. Classification Group Highlighting On Mini Program

Decision: do not add active-group highlighting to `classificationGroups` in the mini program while representative objects remain fully expanded.

Reasoning: the active highlight is useful on H5 because object cards are interactive. In the mini program static reading model, persistent group text plus object text is clearer and avoids introducing state that does not change the learning outcome.

Renderer expectation:

- EdgeOne H5: `classificationGroups` may highlight the selected object's `groupId`.
- Mini Program: `classificationGroups` render as independent static cards.

This is paired with Decision 1.

## 3. Compare Pairs On Mini Program

Decision: `comparePairs` must render both sides and their point lists in the mini program.

Reasoning: unlike representative object expansion, the `a.points[]` and `b.points[]` lists carry core conceptual contrasts. Showing only `childConclusion` drops content and is a parity bug.

Renderer expectation:

- EdgeOne H5: compare cards render side A, side B, their point lists, and conclusion.
- Mini Program: `ComparePairCard` renders side A, side B, their point lists, and conclusion.

This is enforced by `scripts/validate-content-alignment.mjs`.
