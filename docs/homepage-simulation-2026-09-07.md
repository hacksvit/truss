# Homepage and simulation investigation — September 7, 2026

## Findings before implementation

- `member_process.py` publishes useful demand as the lesser of registered maximum and the sum of all device maxima. The example instead set B's wanted set to charger only (170 + 180 = 350 W) and excluded C's charger. The allocator was honoring those invented limits.
- The Three scene steered camera yaw toward movement input, including backward and sideways input. House inspection also replaced the rendered camera while leaving movement active. Input now uses the actual camera direction projected onto the ground, without automatic steering. Inspection freezes movement and returns smoothly to the saved walking view.
- The enclosure door opened 97 degrees toward the camera. Perspective put it over the left hologram. The door now folds 270 degrees around the hinge, against the enclosure side.
- Existing assets include the exact Truss SVG, six topic photos and explanatory diagrams, fonts, palette tokens, and user-provided transparent clouds in Downloads.

## Design plan

1. Preserve the existing homepage module and its dependencies in `web/archive/homepage-2026-09-07`.
2. Build a centered logo and wordmark, one problem sentence and one solution sentence.
3. Tie a finite eight-card story to ordinary page scrolling: fade the introduction, detach its eight endpoint dots and continuously grow those same elements into cards, and move along a perspective carousel with curled side cards. Include buttons and keyboard navigation.
4. End at a spacious footer with a small brand lockup, grouped links, a centered message and oversized logo/wordmark, using the supplied footer image for placement and the existing Truss theme.
5. Reuse layered clouds on the homepage and footer; Example uses only the cloud with the small robot inside it. Cascade layers sideways for route transitions, history navigation and entering/leaving walking mode. Reduced motion uses a static reading layout.

## References and scope

The requested portfolio reference is restricted to the homepage light and dark desktop frames only. Connector design-context, metadata and screenshot calls currently return missing editor access for both provided files, including after the reported access update. The connector identifies `prashumano` as the authenticated account. Browser access did not expose the designs. No unrelated frames were read or edited. Exact Figma frame data remains unverified. The user subsequently supplied light and dark background screenshots; the implementation uses their original textured skies through a CSS crop, with independent cloud PNG layers placed over them. A later supplied muted navy reference replaces the first dark sky. The fixed texture is now shared across every route. Overscan excludes selection borders, a viewport-wide focus treatment spans carousel and footer without a seam, and feathered cloud bases blend into a continuous mist bank. The user then requested larger clouds, reversed orientation and slightly darker blue; these refinements are included.

Implementation references: [Three Camera direction](https://threejs.org/docs/pages/Camera.html), [CSS perspective](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/perspective), [sticky positioning](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/position), [reduced motion](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/prefers-reduced-motion).

## Allocation evidence

The Python allocator on the three configured profiles and a 100 W measurement reserve produces:

| Supply | A | B | C | Rounding remainder |
| --- | --- | --- | --- | --- |
| 900 W | 256 W | 266 W | 276 W | 2 W |
| 1,800 W | 556 W | 566 W | 576 W | 2 W |
| 2,400 W | 756 W | 766 W | 776 W | 2 W |
| 3,200 W | 990 W | 1,040 W | 1,070 W | 0 W |

These are proposals in the standalone three-house example, not live leases from the five-house console. Actual projected draw remains separate: A's binary heater can leave permitted watts unused.


## Final validation

- Production build succeeds (TypeScript and Vite). Vite still notes the existing large application bundle; no build errors.
- All 72 frontend tests pass across 13 suites, including profile/config parity, allocation, camera-relative movement, coordinator return poses, reactive Example supply changes, infeasible supply and robot-cloud mode switching.
- Browser checks covered desktop light/dark appearance, endpoint detachment and rounded-card growth, carousel navigation and its finite ending, clear coordinator panels in both themes, Example's single robot cloud, and a 390 px mobile layout. All eight mobile cards fit without content overflow.
- Lab was checked to use the shared textured background with zero cloud elements. Global background CSS applies to all routes; full cloud stacks render only on Home.
- No Figma files were changed. Existing homepage files remain preserved with rollback instructions in the archive README.


## Final readability adjustment

The user requested a texture-free Three.js frame and much simpler, larger carousel cards. Example now has an opaque smooth gradient inside the scene viewport while the rest of each page keeps the shared texture. Cards grow to up to 640 × 600 px on desktop (88% viewport width on phones). Each has only a two-word topic and one short sentence; earlier photos, category labels and footnotes are removed from the active cards. Title and sentence reveal in a gentle stagger as the card enters focus, with full static text when reduced motion is enabled.
