# Pilot evidence and limits

These are workflow lessons from a local Digimon Survive pilot, not bundled game
data or a certification of future builds. The local source reports were survey
G01, preparation G02/G03, synthesis diagnoses G10/G11b, runtime diagnosis G16,
and AI-listener research R01. No extracted dialogue, original recordings, private
manifest, or account details are included.

| Evidence | Reusable lesson | Limit |
|---|---|---|
| G01/G02 metadata and joined manifest | Trace script voice calls, text keys, speaker keys, and real clips; list unmatched IDs separately | A call count is not a joined-row count |
| G02 loader build and hashes | Late clip-assignment override avoids original bundle writes; strict PCM16 parser and fallback are useful | Initial build/static checks did not prove runtime |
| G03/G10 voice-lock experiments | Own-designed reference plus synthetic prompt continuation reduced pitch drift; preserve accepted source line | Character fit still needs the owner's ear |
| G10/G11b speech gates | Calibrate on actual real Thai speech; speech-only pace correction, separate float/PCM16 flatness, conditional secondary-ASR veto | Cached re-scoring is not new accepted synthesis; missing failed WAVs limit diagnosis |
| G16 diagnosis | Missing fallback fixture, overstrict source-ID equality, conflated exit result, and regenerated config hash caused false failures | Historic split tone could not be fully diagnosed after capture deletion |
| Later G16 coordinator rerun | Second bounded attempt passed READY, tone HIT/duration, existing-original MISS, sequence, single-voice observation, and clean quit; baseline hashes held | First attempt did not pass clean quit; loader tone test is not Thai scene acceptance |
| R01 research and local panel scripts | Listener output needs real audio capability, human calibration, and uncertainty labels | Research suggestions are not runtime proof; panel backend/plots need independent setup |

The G16 worker report and rerun instructions predate the coordinator's later PASS
result. Keep evidence chronology explicit rather than silently treating the older
pending report as final. The public plugin is a generic source template; its
game-specific autotest was intentionally removed. It requires fresh adaptation
and runtime validation. No full-scene owner listening acceptance or executed
uninstall is claimed by this contribution.
