# toscafasso.com — migration inventory (crawled 2026-09-03)

Platform: Squarespace 7.1 (Fluid Engine). Site ID 662160748ff74b53f620dae6.
Fonts: Open Sans, Pontano Sans (served via Adobe Typekit; both are Google Fonts / SIL OFL — free to self-host).
Domain: nameservers = Squarespace DNS (domain registered at Squarespace). Email: Google Workspace (MX aspmx.l.google.com).
Trackers: Reddit ads pixel.

## Live (in navigation)
| URL | Words | Notes |
|---|---|---|
| / | 47 | hero image + IG/LinkedIn + Amazon link |
| /podcast | 186 | Spotify/Apple links, images, no embeds |
| /the-book | 400 | Amazon + B&N links |
| /privacy-policy | 640 | title "Privacy Policy 1" |
| /terms-of-service | 766 | title "Terms of Service 1" |

## Indexed but NOT in navigation (sitemap)
| URL | Words | Status |
|---|---|---|
| /blog + 17 posts + /blog/tag/Podcast | 250–890 each | Real content, orphaned from nav. Keep. |
| /about | 67 | orphan |
| /work-with-me | 212 | orphan |
| /manager-on-a-mission | 343 | orphan |
| /how-we-lead-program | 254 | orphan |
| /newsletter | 65 | Squarespace FORM |
| /lead-magnet-leadership-rx | 79 | Squarespace FORM |
| /good-managers-game-plan | 42 | Squarespace FORM |
| /good-managers-game-plan-1 | 4 | download stub |
| /email-thankyou | 84 | thank-you page |
| /appointments | 28 | Acuity iframe (looks like default placeholder: `squarespace-example`) |
| /toscas-store + 2 products | — | Squarespace Commerce: "1:1 Coaching Package", "NSFW Pre-Order Kindle" (pre-order — book already out) |
| /home, /home-1 "Home (OLD)", /home-2 "Home (Copy)" | 0–182 | duplicates of / |
| /podcast-1 | 250 | duplicate of /podcast |
| /oldthe-book | 405 | duplicate of /the-book |

## SEO issues
- 5 duplicate/legacy pages indexed (home, home-1, home-2, podcast-1, oldthe-book) — split ranking; propose 301s.
- Missing meta descriptions: the-book, privacy, terms, work-with-me, manager-on-a-mission, how-we-lead-program, all stubs.
- "Privacy Policy 1" / "Terms of Service 1" / "Store 1" titles never renamed.
- ~30 pages of real content reachable only by search engines, not by visitors.

## Things a static site cannot do as-is
1. Forms (newsletter, 2 lead magnets) post to Squarespace → need a replacement backend.
2. Store checkout → Stripe Payment Links or drop.
3. Acuity iframe → keeps working only if Acuity subscription kept (likely placeholder anyway).

## Proposed 301s (reports/redirect-map.csv) — awaiting owner confirmation
