# Psychometrics For AI Evaluation

Psychometrics provides tools for asking what a test measures and how stable its measurements are. For AI evaluation, those tools need careful adaptation because the "respondents" are model systems and the items may contain formatting artifacts, memorized text, or scoring shortcuts.

## Response Matrices

The basic object is a model-by-item response matrix. Rows are models, columns are benchmark items, and values are binary or continuous scores.

## Difficulty

Difficulty is estimated from the fraction of models that answer an item correctly. Very easy or very hard items can still be useful for some claims, but they often provide little ranking information in a narrow model panel.

## Discrimination

Discrimination estimates whether higher-scoring models are more likely to answer an item correctly. `valideval` uses a proxy correlation rather than overfitting a fragile parametric model. The primary field is an anchor-oriented Spearman correlation between item correctness and model score on positively oriented anchor items; corrected item-total correlation is also reported as `corrected_item_total_correlation`.

Negative-discrimination flags are evidence consistent with an item rewarding the wrong behavior under the observed model panel. They require caution when the panel is small or when too few clean anchor items remain to orient the ability axis.

## Model Ability

The v0 IRT diagnostic reports a latent-ability proxy derived from model score patterns. It is useful for comparing rankings under assumptions, not for declaring a true capability order.

## Uncertainty

Bootstrap intervals are used where simple and meaningful. Small model panels and sparse matrices should be treated as high-uncertainty regimes.
