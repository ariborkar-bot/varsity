# Put Varsity on the App Store (for whoever owns the Apple Developer account)

You need a Mac with Xcode, Node 20+, and the Apple Developer account that owns the "Varsity Fantasy" record in App Store Connect.

## 1. Open the iPhone project (no Node needed)
The Xcode project is already generated and committed in `native/ios`. Get the repo (Code > Download ZIP on GitHub, or `git pull`), then double-click `native/ios/App/App.xcodeproj`. Xcode opens and downloads the Swift packages by itself the first time (needs internet, takes a minute).

(Only if the web app changed and you want those changes in the iPhone app: with Node installed, run `cd native && npm install && npm run sync`, then commit `native/ios`.)

## 2. In Xcode
1. Click **App** (blue icon, top of the left list), then **Signing & Capabilities**. Choose your Team. (Xcode menu > Settings > Accounts > + to add the Apple ID first.)
2. **Bundle Identifier** must be exactly the one in App Store Connect. The project uses `com.varsityfantasy.app`. If App Store Connect shows a different one, change it here.
3. Already done for you: AdMob test app id in Info.plist, iPhone-only, portrait-only, 1024 icon (a sharpened 512 version, replace with a true 1024x1024 when you have one), Version 1.0, Build 1. Every new upload needs a higher Build number (General tab).
4. Top bar: pick **Any iOS Device (arm64)**. Then **Product > Archive**. When Organizer opens: **Distribute App > App Store Connect > Upload**.
5. After 5-30 min the build shows under App Store Connect > TestFlight > Builds. Install it on a phone with TestFlight and test sign-in, a pack, and "Watch a sponsor".

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
