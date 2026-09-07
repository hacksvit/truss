# Info and Credits: motion directions

Implementation: `/info` now contains the twelve-chapter unfolding-building walkthrough,
with chapter navigation, local SVG scenes, both themes, a phone layout and static
illustrations when reduced motion is enabled. `/credits` has the five-card arrival
layout; confirmed team names, contributions and portraits are still pending.

## Recommended Info concept — A building that opens up

The homepage introduces the idea through the logo. Info should explain it through
one continuous illustrated building, with the camera following the explanation.
The visitor scrolls normally; each section changes the scene and reveals a short
heading plus one or two lines. The text holds still long enough to read.

### Storyboard and proposed page copy

| Topic | Visitor-facing copy | What moves |
|---|---|---|
| Shared Supply | Several rooms share one power supply. When everyone needs more at once, something has to wait. | A small building rises into view. Lights appear room by room; a shared supply line brightens. |
| Room Agent | A small program looks after each home’s appliances. A room could be managed the same way. | The facade opens like a dollhouse; one room comes forward and its agent marker wakes up. |
| Local Choice | The agent chooses what can run within its allowance. Appliance details stay out of the coordinator’s view. | Appliance icons stay inside the room while its outer wall becomes translucent. |
| Small Request | The home sends how much power it could use. The coordinator receives a total, rather than an appliance list. | A single request capsule leaves the room and follows a curved route to the coordinator. |
| Essentials First | Each home has an agreed basic allowance. We reserve those allowances before sharing extra power. | Thin bands under every room fill first; their labels remain fixed. |
| Fair Shares | Spare power is shared fairly until each home’s request is filled. A smaller request leaves more for the others. | Columns rise together; a satisfied room stops filling while the others continue. |
| Kept Promises | Earlier permissions may still be in use. We count them before giving out more power. | Faint earlier permission bands remain on the scene; a new band fits into the remaining space. |
| Short Permission | Extra power comes with an expiry. If renewal stops, the virtual home returns to its basic allowance. | A ring gently unwinds and only the extra band recedes. The room remains visible. |
| Missing Readings | No reading means “unknown.” We keep counting earlier promises until they expire. | One reading becomes an outlined question mark; its reserved band stays. |
| More Rooms | More rooms would mean more agents and messages. We need to test the whole system as it grows. | Camera pulls back to reveal repeated room outlines. Label this illustration “proposed expansion.” |
| Tested Today | The live demo runs five virtual homes. The Lab tests allocation for larger groups, not the whole network. | Five rooms stay filled; the larger outline grid fades into a separate Lab panel. |
| Real Limits | Software cannot create missing power. Real installations need suitable hardware and further testing. | The building settles beside the supply limit, with links to Example and Lab. |

The room-agent phrasing is intentional: the implemented unit is a household/member,
not a verified agent installed in every real room. Privacy here means keeping details
out of the coordinator's view; the demo observer can see them. “More Rooms” must not
present the Lab's allocator-only measurements as proof of a deployed large network.
These distinctions come from README's How it works and Scope and limits, and the
current member, plant, coordinator and observer code.

### Motion structure

1. **Open:** supply, building, then a single room (first three topics).
2. **Follow:** request out, fair allocation, permission back (next four topics).
3. **Interrupt:** expiry and missing readings; keep the building stable (two topics).
4. **Pull back:** scale, current proof, next steps (last three topics).

Use a persistent SVG/isometric scene beside the copy on desktop. Interpolate camera
position and vector paths with scroll; animate transforms and opacity, not text
character by character. Each chapter spends roughly its first quarter transitioning
and the rest holding. Include ordinary chapter links so visitors can skip ahead.
On mobile use scene above copy and shorter chapter holds. Reduced motion shows the
same ordered illustrations and copy without a pinned scene. No clouds here; retain
the shared textured background, with a smooth surface immediately behind the scene.

### Alternative directions

- **Follow one request:** travel along a single illuminated route, from room to
  coordinator and back. More compact, but the scale discussion feels less natural.
- **Blueprint layers:** separate building, agent, messages and authority into sheets
  that slide apart. Visually precise, but risks feeling like a technical diagram.

The opening building combines the clearest everyday metaphor with enough room for
the later failure and scale topics. Avoid copying the homepage carousel or adding
free camera controls; the visitor should be able to read without learning navigation.

### Assets

No new assets are required for a first implementation: existing local building,
robot and appliance models can guide simple original SVG room illustrations.
For a more polished art direction, supply one layered room/building illustration
(SVG or transparent PNG parts): facade, interior, lamp, appliance, and agent. Keep
the camera angle and lighting consistent. No embedded words. Avoid a single flat
image if its walls or objects need to move independently.

## Credits concept — Five people, one team

Five portrait cards approach from alternate sides with a small tilt and depth change.
Each settles into its own place, instead of orbiting or becoming a carousel. Once
the fifth arrives, a fine line joins the group and the closing message appears:
“Different strengths. Something shared.” The five cards remain equally sized.

A first motion layout is implemented at `/credits`. Names, photographs and
contributions are explicitly pending, not inferred from Git history or planning roles.
Desktop arrival follows scroll; smaller screens use a staggered two-column layout.
Reduced motion presents the complete team immediately.

Each finished card contains only a portrait, name and roughly six-word contribution.
Possible writing styles (examples, not assigned credits):

- Made power sharing fair for everyone.
- Built the agents inside each home.
- Kept messages moving between the homes.
- Turned complex ideas into clear visuals.
- Tested failures and shaped the demo.

Needed: five preferred display names, five actual contribution summaries, five
portraits. Ideally portraits are at least 800 × 1000 pixels with room around the
face for a 4:5 crop. Natural portrait backgrounds work; cutouts are optional.
Final word choices must reflect what each person actually did.

## Credits: further exploration

The current five-card arrival is a working starting point. For the next version,
the motion should explain collaboration while giving every person equal space.
The portraits, names and six-word contributions stay readable once they arrive.

### Recommended — Five connections

Opening: “Five people. One shared idea.” Five small illuminated points sit at
different positions across the scene. They are independent points, not pieces
of the Truss logo.

1. As the visitor scrolls, a thin curved line draws from the first point to the
   second. The first two portraits are uncovered by a vertical mask inside
   already full-size frames. Nothing grows from a dot into a card.
2. The line continues to the next three points. Each portrait is uncovered in
   turn, with its name and short contribution appearing just after it.
3. The line completes a loose loop behind all five people. Their cards gently
   straighten and settle into a three-above, two-below arrangement. All five
   have the same size, brightness and reading time; there is no central leader.
4. A shared closing line appears: “Different strengths. Built together.” A
   GitHub link sits beneath the group.

Hover or keyboard focus can gently lift one card and brighten its segment of
the connecting line. Names and contributions must already be visible; interaction
is a small finishing detail, not a requirement for reading.

Why this direction: the homepage is about taking an idea apart, Info is about
looking inside the system, and Credits becomes about people joining together.
It feels related to Truss without repeating either page's animation.

### Alternative — The worktable

Five portrait prints slide onto a virtual desk from different directions. Each
lands with a small tilt, followed by a simple caption, then the camera pulls
back to show the whole team. Warmer and more personal, but the desk needs subtle
art direction to fit the sky and architecture theme. Avoid physics bouncing
and overlapping names. Ordinary photos work well here.

### Alternative — Five windows

A building silhouette has five equally sized windows. Shutters open one at a
time to reveal the people; the silhouette recedes, leaving clean portrait frames.
This relates directly to the project, but repeats the opening-room metaphor
from Info. Choose it only if a very unified visual story matters more than
giving Credits its own identity.

### Practical shape

- Desktop: a short two-to-three-viewport sequence ending with all five visible.
- Phone: one large portrait at a time in normal vertical flow, with the line
  continuing between entries. Each mask reveals as that portrait enters view.
- Reduced motion: show all portraits and captions immediately, with the line
  already drawn. No camera movement or pinned scrolling.
- Both themes: use solid caption surfaces, keep the photos in natural colour,
  and change the line and frame colours with the theme.
- Assets: five ordinary portraits with a consistent crop. No special animation
  files or cutout photos needed. Transparent portraits are optional.

Pending content remains the five preferred names, portraits and true contributions.
For each person, a plain description of their work is enough; we can edit that
into a six-word caption without inventing responsibilities.
