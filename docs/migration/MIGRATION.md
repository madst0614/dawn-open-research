# Migration ledger

No DAWN-SRW code was copied or refactored into this repository during bootstrap. The public program references its MIT-licensed repository at commit `30165201e68897d75f0586805d321393159550c3` and invokes its zero-shot evaluator through a local subprocess adapter. The implementation's license and commit remain distinct from this repository's Apache-2.0 license.

Future code migrations must record original repository, path, commit, new path, reason and license review here. Never migrate credentials, `.env`, virtual environments, local caches, outputs, large checkpoints or machine-specific configuration.
