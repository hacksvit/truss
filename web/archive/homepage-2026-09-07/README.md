# Homepage before the September 7 rebuild

This is a byte-for-byte snapshot of the original Showcase page, its PixelText and TopicArt components, and the shared shell/style entry points before this change. The original images in web/public/topics and the shared components remain in place.

To restore only the old homepage, run from the repository root:

```sh
cp web/archive/homepage-2026-09-07/src/routes/Showcase.tsx web/src/routes/Showcase.tsx
```

The old `.showcase` / `.reel-*` rules are still in `web/src/chrome.css`. The new homepage stylesheet is imported only by the new Showcase module, so replacing that module also stops loading its styles. The Example allocation and movement fixes remain intact.

The other archived shell/style files are reference copies. Do not restore them wholesale unless you also intend to undo shared navigation changes.
