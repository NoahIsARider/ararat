# Independent art and experience audit

**Current review:** the structural and narrative re-review dated 21 November 2026, below, supersedes the earlier prototype's geometry, runtime counts and wordless-presentation assessment. Earlier observations are retained as historical evidence, not as validation of the rebuilt vessel.

Reviewed by the separate `art_audit` agent on 21 November 2026 (Asia/Shanghai).

## Verdict

**Accepted as an explorable environment prototype and editable Blender asset handoff. The requested commercial visual benchmark of _What Remains of Edith Finch_ has not been achieved. This is not a Steam release candidate.**

The project now communicates an immense weathered ark, newly exposed wet earth, small signs of returning life, and a cold mountain setting. Its quiet, wordless presentation is consistent with the brief. Further art direction, asset finishing, narrative work and game-engine validation are required before treating it as a production environment.

## Evidence and scope

I directly inspected `artifacts/arrival.png`, `olive.png`, `threshold.png`, `interior.png`, `valley.png`, `growth.png` and `mountains.png` generated around 16:28, then rechecked the updated threshold and interior views around 16:31. I also reviewed `src/main.js`, `scripts/build_scene.py`, `scripts/environment_detail.py`, the verification script and its JSON report.

I directly inspected the final native Blender validation image, `artifacts/blender-preview.png`, generated at 16:38:54. It is an Eevee render of the final source scene; the source file retains Cycles settings. The earlier Cycles cover in `artifacts/archive/early-blender-cover.png` is excluded from final evidence. No final Cycles-quality output is claimed.

The native preview confirms that the ark, gangway, layered mountains, shore materials and contact rocks exist in the authored Blender scene. Its fog and sky fill still produce a pale, low-contrast result: timber grain remains visible, but the mud's ochre and the olive branch's visual importance are weaker than in the browser. The two renderers therefore do not yet have matching final art direction. Browser animation, walking and audio are runtime features, not native Blender gameplay.

The verification report records 567,152 triangles, 2,341 source meshes, 19 material batches and 53 full-frame draw calls in the tested view. It reports no runtime errors, real keyboard movement of approximately one metre at arrival, and no failures in the controller's continuous shore/ramp/interior/return route logic. This does **not** establish full-route keyboard playtesting, capsule collision quality, target-hardware frame rate, controller support or Steam compatibility.

## Requirements assessment

| Requirement | Assessment |
| --- | --- |
| Ark timber | Recognizable grain, separate boards, seams, structural ribs and pegs. Photographic PBR maps improve close views. Hero-object UVs and wear still need finishing. |
| Olive branch | Fully visible on its shore stone and repeated at the interior offering table. Leaf shape and pale undersides are readable. Arrangement remains more regular than a natural cutting. |
| First exposed earth | Ochre-grey mud, darker sediment, footprints, driftwood and standing water communicate retreating floodwater. Wetness variation is substantially improved. |
| Mountains | Broad overlapping ridges and mist establish scale. The earlier needle peaks and artificial blue cascade ribbons were removed. Surface form remains visibly procedural. |
| New vegetation | Sparse grass clusters, fern fronds, seedlings and broken moss patches preserve large areas of washed ground. Close-view botanical shading still needs refinement. |
| Wordless immersion | No modern text, menus or HUD appear in the reviewed views. No written scroll was added. Controls are documented outside the scene. |
| Exploration | Shore, gangway, threshold and interior are connected by the prototype controller. Interaction and production collision remain limited. |

## Corrections made after audit feedback

The implementation corrected near-black soil, paper-like diamond leaves, the obscured shore branch, excessively bright rock colours, conspicuous uniform sediment ropes, widespread hull light leaks, an entrance rib crossing the opening, floating mountain-foot stones and implausible parallel waterfall strips. The final lighting revision also removed the artificial golden hotspot at the gangway landing and reduced timber reflections; the interior remains legible. These are meaningful improvements; they do not by themselves establish commercial quality.

## Remaining production priorities

1. **Light and material response.** The landing hotspot is fixed. Some high-frequency floor highlights and stretched grain remain, and the interior still has limited localized light hierarchy. Refine UVs and specular anti-aliasing, and art-direct a restrained focal area against the cold exterior. Shape cloud openings and shadow masses more intentionally. In Blender, further balance fog, sky fill and exposure so the cold atmosphere retains darker contact shadows, readable ochre earth and a clear olive focal point; validate this in the intended final renderer.
2. **Geology and terrain transitions.** Replace smooth procedural mountain undulations with authored primary ridges, branching erosion, broken strata and convincing scree transitions. Refine puddle shorelines and sediment masks rather than relying on flat silhouettes or uniform material coverage.
3. **Hero asset finishing.** Correct stretched timber/end-grain UVs, standardize texel density, and add purposeful cuts, joinery, caulking, water staining and local wear. Improve leaf asymmetry and translucency; moss still reads as discrete patches rather than fine growth.
4. **Environmental storytelling.** The offering table and empty stalls establish an idea, but the voyage needs richer, specific traces of use, repair, loss and survival. Build a sequence of discoveries and changes in enclosure, sound and view instead of adding undirected clutter.
5. **Game production.** Author collision meshes and LODs; validate texture memory, lighting and material behavior in the chosen engine; test the complete route with real controls and target hardware. Integrate the game's movement, interactions, accessibility, saves and packaging. Preserve and review `ASSET_CREDITS.md` with the handoff.

The appropriate next milestone is a focused vertical slice: finish the shore olive stone, gangway, doorway and offering table to one consistent standard, then validate that sequence in the intended game engine.

## Structural and narrative re-review — 21 November 2026

Independently reviewed by the separate `structure_review` audit agent. I read `scripts/ark_structure.py`, `scripts/rebuild_ark.py`, `scripts/exile_boat.py`, `src/navigation.js`, relevant runtime loading code, `artifacts/structure-verification.json`, `artifacts/verification.json` and `artifacts/story-verification.json`. I inspected the rebuilt threshold, stair side and doorway, then directly rechecked the final approximately 17:48 browser captures `stair-side.png`, `door-joint.png`, `stern.png`, `bow.png`, `roof.png` and `exile-wide.png`. I also inspected the approximately 17:37–17:38 `story-prologue.png`, `story-ending.png` and `story-afterglow.png`, and rechecked the final integrated verification reports written at 17:49. Finally, I directly inspected `artifacts/blender-preview.png`, generated at 17:51:39 from the final source scene in Eevee. Cycles settings remain in the source; this image is not a final Cycles render.

**Scoped verdict: the rebuilt ark entrance and timber staircase are coherent enough for this playable prototype, and the small boat supports the departure narrative. No major detached stair frame, obvious open transom hole or broad deck protrusion is visible in the reviewed final views. This remains below the requested _What Remains of Edith Finch_ commercial benchmark and is not a Steam release candidate.**

| Area | Evidence and assessment |
| --- | --- |
| Hull and ends | A continuous inner skin backs separate cedar courses and closes the bilge and transoms. The final bow/stern views no longer show the earlier checker artifacts at the end joints. The topology report records zero boundary and non-manifold edges for the evaluated solidified skin. This establishes a manifold wall object, not a watertight enclosed vessel: the hatch and clerestory ventilation remain open, and the complete assembly was not Boolean-unioned or leak-tested. |
| Stairs and landings | The 28 horizontal treads have approximately 0.174 m rise and 0.357 m going. The last tread and upper platform meet the 4.97 m deck elevation. Closed risers, housed side stringers, bearing caps, paired uprights and crossed braces read as a connected timber assembly. All ten pad bounds intersect their sampled terrain elevation; this does not certify every pad corner or physical load capacity. |
| Hatch and deck | Built-out coaming cheeks bridge the curved side to vertical jambs, and the sill/platform/floor transition is visually continuous in the doorway capture. Deck geometry follows the hull plan. Navigation half-width tapers from about 3.90 m amidships to 1.60 m at the reviewed end stations, rather than retaining the old rectangular walkable area. |
| Posts, roof and ropes | Interior uprights, cross ties and knees form a readable frame. The rafters are now seated below the outer weatherboard plane. Roof seam battens replace the former dotted roof pattern with coherent timber strips in the final roof capture. Handlines terminate at actual post/jamb wraps, with visible sockets and pegs. These are plausible visual contacts; they are not a complete joinery or engineering audit. |
| Shore boat | The hull, gunwales, ribs, clipped sole, supported thwarts, oar, bundle and rope read as one craft. It faces open water away from the ark. Its authored bottom extends below the shared sea level, so intended flotation is not counted as an unsupported-geometry fault. The low oblique view still has weak water contact: a waterline stain, meniscus and subtle wake would improve weight and immersion. |

The browser report records 1,200,366 triangles, 3,400 source meshes, 35 material batches and 76 draw calls in its tested view. It reports no runtime errors, no sampled navigation failures, and actual keyboard movement from the stair foot through the hatch into the interior and back. This is stronger route evidence than the earlier analytic controller check, but it does not establish comprehensive collision coverage, frame rate, accessibility, controller support or target-hardware performance.

The revised story intentionally supersedes the earlier wordless brief assessment. Warm-white, thick handwritten English prose floats directly over the scene without parchment, border or buttons in the reviewed captures. It is readable at the captured 1440×900 resolution. The story report confirms the Caveat Brush font loaded, all three memories were registered, early departure was gated, the boat actually moved, and the ending was reached without reported errors. The orange-red sky, low sun, golden reflection and bow framing clearly communicate departure and self-exile. The report is automated route evidence; no claim is made for literary polish, localization, screen-reader access or every viewport size.

The final native Eevee preview confirms the rebuilt hull, covered roof seams, entrance and supported staircase in the authored Blender scene. No obvious detached stair frame is visible in that view. It is substantially paler and flatter than the browser: mist and sky fill weaken timber contrast, pad contact shadows and the shore olive focal point. Its camera does not include the small boat, so that image alone cannot validate the boat's native water contact. Browser story overlays, camera travel and sunset progression are runtime features. This confirms the structural handoff while leaving renderer parity unresolved.

Remaining priorities are visible rather than hidden by the scoped acceptance: roof strips still produce hard, repetitive high-frequency edges at a distance; end-grain/side-grain consistency and some stretched timber UVs need finishing; contact shadows, shoreline transition and boat water interaction need refinement. Roof-only runtime shadow reception is disabled in the reviewed implementation, and the native preview does not establish matching roof lighting. The terrain, geology and botanical assets retain the earlier procedural character. A focused production pass should resolve those issues and validate the final renderer, collision, memory, performance and packaging before any commercial-quality claim.

## Passage fades and ending loop — narrow interaction re-review

The independent `structure_review` agent reviewed the revised `src/story.js`, `src/style.css`, browser story test and updated `artifacts/story-verification.json`, and directly inspected `story-fade-to-black.png`, `story-black.png` and `story-restart.png`. No blocking transition race, skipped-passage path or stale-timer/reset error was found in this scope. Epoch-guarded timers and visible-state input gating protect page changes; the forced initial layout resolves the first-frame fade coalescing concern.

Text now fades in over 1.8 seconds and out over 1.5 seconds with a 0.3-second page pause. CSS animates opacity only. Browser evidence records intermediate opacity on both initial and restarted prologues, zero vertical translation, unchanged outgoing text position and ignored rapid input during its fade. After the last passage, the ending holds briefly, fades to full black, resets camera/FOV, boat, memories and story state behind that cover, then reveals the opening and its first passage again. The inspected screenshots and report agree on full black and the restored opening; the report records no runtime errors and retains the passing memory/departure/moving-boat/ending checks. This accepts the requested prototype interaction iteration, without expanding the earlier renderer, performance or commercial-readiness claims.
