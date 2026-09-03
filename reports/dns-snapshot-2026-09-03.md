# toscafasso.com — DNS snapshot (Phase 1, before any changes)
Captured: 2026-09-03, via `dig` against public resolvers.

## Nameservers (current)
Hybrid: Squarespace uses NS1 as backend + its own NS:
- dns1-4.p01.nsone.net
- ns01-04.squarespacedns.com

## MX (Google Workspace)
```
1  aspmx.l.google.com.
5  alt1.aspmx.l.google.com.
5  alt2.aspmx.l.google.com.
10 alt3.aspmx.l.google.com.
10 alt4.aspmx.l.google.com.
```

## A (root — Squarespace website hosting)
```
198.185.159.144
198.185.159.145
198.49.23.144
198.49.23.145
```

## www
CNAME → ext-sq.squarespace.com.
(also resolves to the same 4 A records above)

## TXT (root)
```
google-site-verification=8QwTx1OiJulB0fq3rMM6bi1XQPul5905c20x0PaTb44
```
This is a Google Search Console / domain-wide verification token — **must be
recreated in Cloudflare** or Search Console access breaks.

## SPF
**None found.** No `v=spf1` TXT record exists at the root today. Nothing to
preserve here — but also means outbound Workspace mail today has no SPF
alignment, which is worth knowing regardless of this migration.

## DKIM
**None found** at `google._domainkey` or other common selectors. Workspace's
DKIM signing does not appear to be turned on for this domain currently.

## DMARC
```
_dmarc.toscafasso.com  TXT  "v=DMARC1; p=none"
```
Permissive policy — keep as-is through the migration.

## autodiscover
No record.

---
## Cloudflare zone (created)
Zone added to Cloudflare on Free plan. Scan found 4 A, 2 CNAME, 5 MX, 2 TXT —
matches this snapshot exactly (plus Squarespace's `_domainconnect` CNAME,
harmless, left as-is for now).

Assigned Cloudflare nameservers:
```
dakota.ns.cloudflare.com
deb.ns.cloudflare.com
```

## Phase 4 — Cutover executed
Nameservers switched at Squarespace to the Cloudflare pair above. Confirmed
via `dig NS toscafasso.com` from two independent resolvers (default + Google
8.8.8.8) showing Cloudflare already; Cloudflare's own resolver (1.1.1.1) was
still caching Squarespace's NS as of this check — normal, propagation window.

**72-hour soak starts now.** Do not cancel Squarespace or Google Workspace
until:
- Inbound mail to tosca@toscafasso.com is confirmed landing in
  tosca.fasso@gmail.com (send a real test email once propagation settles)
- Tosca has completed Gmail "Send mail as" for tosca@toscafasso.com and sent
  a test reply that arrives without landing in spam
- The site (toscafasso.com, once deployed to Cloudflare Pages) is confirmed
  resolving correctly
- No bounces or missing-mail reports for 72 hours

Rollback path if needed: Squarespace → Domain Nameservers → "Use Squarespace
nameservers" button restores the original 8 nameservers automatically.

## Propagation check-in log
- ~10:5x UTC: NS switched at Squarespace. Initial dig from default resolver
  and 8.8.8.8 showed Cloudflare NS already; 1.1.1.1 still showed Squarespace.
- Sent test email to tosca@toscafasso.com from hellocward@gmail.com.
- Follow-up check: MX for toscafasso.com reverted to showing Google's
  aspmx.l.google.com records on ALL resolvers checked (default, 1.1.1.1,
  8.8.8.8) — NS also back to Squarespace's on 1.1.1.1. Propagation is not
  monotonic while caches expire at different times across resolvers/TTLs.
- Test email not found in tosca.fasso@gmail.com inbox or spam as of this
  check — consistent with MX still pointing at Google Workspace. No bounce
  either, so it's most likely sitting in the still-live Workspace mailbox.
- Action: wait and re-check periodically rather than resending repeatedly.
  Don't start Tosca's Gmail Send-As step until MX resolves to Cloudflare
  consistently and the test email is confirmed delivered via the new route.

---
## Rollback reference
If anything goes wrong after nameserver cutover (Phase 4), point
toscafasso.com's nameservers back at:
```
ns01.squarespacedns.com.
ns02.squarespacedns.com.
ns03.squarespacedns.com.
ns04.squarespacedns.com.
```
(via Squarespace's own domain settings — this restores the exact state
captured above.)
