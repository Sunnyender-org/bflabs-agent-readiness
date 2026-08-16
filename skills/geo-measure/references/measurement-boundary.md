# Measurement Boundary

## Valid sample

A valid observation is a complete `model-answer` with no exclusion reason. `network_status=verified` additionally requires explicit network evidence. An ordinary web search result is never a model answer, even if it links to the target site.

## Denominators

- Network rate: valid model answers with known network status.
- Site citation rate: valid model answers with verified network use.
- Content absorption, brand mention, recommendation, and dynamic fact accuracy: valid model answers where that field is known.

Every metric reports numerator, denominator, exclusions, missing values, rate, denominator rule, and a 95% Wilson interval. If the denominator is zero, rate and interval are `null`.

## Interpretation

Aggregates remain descriptive and are stratified by platform and terminal. Small, user-supplied, or convenience samples do not support causal conclusions. Readiness and answer observations do not establish traffic, conversion, or revenue.
