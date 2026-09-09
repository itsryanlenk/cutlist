<!--
Thanks for contributing. Keep the pull request small and single-purpose. See
CONTRIBUTING.md for the full bar. Delete any section that does not apply.
-->

## What this changes

<!-- One or two sentences: what is different after this merges, and why it mattered. -->

## Proof

<!-- Paste the RESULT line from the self-test. If you changed a script, paste it from
before and after. -->

- [ ] `bash tests/selftest.sh` passes (`RESULT: 13 pass, 0 fail`)
- [ ] If a script changed, the self-test exercises the new behavior

## The rules

<!-- If this touches clip length, the sync tolerance, the validator limits, or the
trifecta rule, name the dated entry you added to docs/DECISIONS.md and its source.
Otherwise write "n/a". -->

- DECISIONS.md entry:

## Leak check

- [ ] No real episode, caption file, channel profile, guest name, handle, or link in any
      tracked file
- [ ] No em dashes, American English, no creator data in examples
