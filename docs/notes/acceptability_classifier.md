# Acceptability Classifier

This is an optional, tiny supervised diagnostic model. It is not the core contribution of the project.

Task: predict whether a model output is human-acceptable using automatic metric features, model identity, and entity type.

- train rows: 320
- test rows: 80
- split seed: 4652

| system | accuracy | precision | recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| `majority_baseline` | 0.6875 | 0.6875 | 1.0 | 0.8148 |
| `metric_rule_baseline` | 0.5125 | 0.9 | 0.3273 | 0.48 |
| `logistic_regression` | 0.775 | 0.8627 | 0.8 | 0.8302 |

Use this only if the final report needs an explicit trained ML component; otherwise keep it as an appendix or robustness check.
