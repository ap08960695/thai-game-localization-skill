# Pilot evidence and limits

These are workflow lessons from a local Unity Mono pilot, not bundled game data
or a certification of future builds. They describe general dubbing workflow
choices; no extracted dialogue, original recordings, private manifest, or account
details are included.

| Evidence | Reusable lesson | Limit |
|---|---|---|
| Metadata and joined manifest | Trace script voice calls, text keys, speaker keys, and real clips; list unmatched IDs separately | A call count is not a joined-row count |
| Loader build and hashes | Late clip-assignment override avoids original bundle writes; strict PCM16 parser and fallback are useful | Initial build/static checks did not prove runtime |
| Voice-lock experiments | Own-designed reference plus synthetic prompt continuation reduced pitch drift; preserve accepted source line | Character fit still needs the owner's ear |
| Speech gates | Calibrate on actual real Thai speech; speech-only pace correction, separate float/PCM16 flatness, conditional secondary-ASR veto | Cached re-scoring is not new accepted synthesis; missing failed WAVs limit diagnosis |
| Runtime diagnosis | Verify fallback fixtures, ID expectations, exit-state reporting, and config hashes before interpreting results | Missing captured artifacts can prevent later diagnosis |
| Bounded runtime check | Check plugin readiness, replacement/fallback behavior, sequence, voice count, clean quit, and baseline hashes | A loader tone check does not establish in-game Thai scene acceptance |
| Listener research and panel scripts | Listener output needs real audio capability, human calibration, and uncertainty labels | Research suggestions are not runtime proof; panel backend/plots need independent setup |

The public plugin is a generic source template; its game-specific autotest was
intentionally removed. It requires fresh adaptation and runtime validation. No
full-scene owner listening acceptance or executed uninstall is claimed here.
