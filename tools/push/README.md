# Varsity phone notifications (Web Push)

How it works: a phone that turns on notifications subscribes to Web Push and saves the subscription (`push_save`, tools/sql/push.sql).
Every 5 minutes GitHub Actions runs `send.mjs`, which works out which alerts are due (`plan.mjs`) and sends them. Closed apps get them too.

Alerts: game start (an hour before tip-off, your profile school), 5 Card Draw hand not dealt (basketball: 90 min before the first tip; football: 4 PM on game days),
final score of your school's game, league chat messages, Sunday 5 PM recap. Each phone's alert choices and quiet hours (default 9 PM-8 AM) are saved with the subscription.

## One-time setup (owner)
1. Supabase SQL editor: run `tools/sql/push.sql`.
2. GitHub repo > Settings > Secrets and variables > Actions > New repository secret, three of them:
   - `SUPABASE_URL` = https://urdkamhsdjhzhrjwzyoq.supabase.co
   - `SUPABASE_SERVICE_KEY` = the **service_role** key (Supabase > Project Settings > API). Never put it in the app or the repo.
   - `VAPID_PRIVATE_KEY` = the private key that matches `VAPID_PUB` in index.html (also used in `.github/workflows/push.yml` as the public key).
3. GitHub > Actions > "Send phone notifications" > Run workflow with Dry run ticked once: the log lists who would get what.
4. Turn on phone notifications in the app (bell > settings). The app only stops showing its own system notifications once the sender has run in the last 45 minutes.

Changing the VAPID keys: `npx web-push generate-vapid-keys`, replace `VAPID_PUB` in index.html and the public key in push.yml, update the secret; phones re-subscribe on their next app open only if they unsubscribe first, so avoid rotating.

## Tests (no network)
`cd tools/push && npm ci && node test.mjs && node test.send.mjs`

## Notes
- Game times are Pacific. A game with no listed time counts as 7:00 PM.
- Pick 'em league locks and "your matchup finished" alerts are not sent yet (they need the app's league logic); the in-app bell still shows them while the app is open.
- iOS only delivers Web Push to Varsity added to the Home Screen. Every push must show a notification, so the service worker never skips one.
