PATCH

**`slipwai` no longer writes an interpreter cache (`__pycache__/`) beside its bundled backing-service assets when it loads their prune script.** Loading the script left a `.pyc` under `assets/backing-services/` of the checkout it ran from, which the factory's own gate counted as a change to the tree, so a passing run could never be reused. The script is now loaded with bytecode writing off, as the style checker beside it already was.
