# Put Varsity on the App Store (for whoever owns the Apple Developer account)

You need a Mac with Xcode, Node 20+, and the Apple Developer account that owns the "Varsity Fantasy" record in App Store Connect.

## 1. Build the iPhone project (about 10 minutes)
```
git clone https://github.com/ariborkar-bot/varsity
cd varsity/native
npm install
npx cap add ios
npm run sync
npx cap open ios
```
(`npm run sync` copies the web app into the iPhone project. Run it again after every app change.)

## 2. In Xcode
1. Click **App** (blue icon, top of the left list), then **Signing & Capabilities**. Choose your Team.
2. **Bundle Identifier** must be exactly the one in App Store Connect. The project uses `com.varsityfantasy.app` (set in `capacitor.config.json`). If App Store Connect shows a different one, change it here and in that file.
3. Open `App/App/Info.plist` and add key `GADApplicationIdentifier` (string) = `ca-app-pub-3940256099942544~1458002511` (Google's test ad id; swap for the real one before earning money).
4. Under **General**, set Version `1.0` and Build `1`. Every new upload needs a higher Build number.
5. Replace the app icon in `App/App/Assets.xcassets/AppIcon` with a 1024x1024 PNG (no transparency, no rounded corners).
6. Top bar: pick **Any iOS Device (arm64)**. Then **Product > Archive**. When Organizer opens: **Distribute App > App Store Connect > Upload**.
7. After 5-30 min the build shows under App Store Connect > TestFlight > Builds. Install it on a phone with TestFlight and test sign-in, a pack, and "Watch a sponsor".

## 3. App Store Connect listing (Distribution tab)
- Screenshots (6.9" and 6.5" iPhone), description, keywords, support URL, **privacy policy URL** (the app has a privacy page; its `[contact email]` placeholder must be filled in first).
- Age rating: answer the questions honestly. Tokens and picks count as simulated gambling, which pushes the rating to 17+.
- App Privacy: collects email and account info (Supabase), uses AdMob ads.
- App Review notes: give a **demo login** (a real test account), since the app requires sign-in.
- Apple requires an **in-app way to delete the account** for apps with sign-up. Check Settings has it before submitting.
- Select the build, then **Submit for Review**.

## Things that can get it rejected
- Looking like "a website in an app" (Guideline 4.2): the real AdMob ads, push alerts and haptics help.
- Real-money purchases must use Apple in-app purchase. Today real-money packs say "Coming soon" and tokens have no cash value, which is fine.
- Using real player names and stats commercially without a data license.
