# Changelog

Tracks fixes and features pulled into this fork's `develop` branch, including
those adapted from upstream `ideoforms/AbletonOSC` pull requests. See
`notes/pr-triage.md` for the full triage of upstream PRs this fork is
tracking.

## Unreleased

- Fixed `send()` swallowing benign `ConnectionResetError` (WSAECONNRESET) as
  an error-level log instead of the benign warning already used for the same
  condition on the receive path. Based on upstream PR #214.
- Added `/live/clip/get/groove`, returning the assigned groove's name (or an
  empty string) — `clip.groove` previously couldn't be queried at all because
  the raw `Live.Groove.Groove` object isn't OSC-serializable. Based on
  upstream PR #203.
