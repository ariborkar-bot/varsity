# Varsity native app (iOS + Android) with real rewarded ads

The web app is wrapped with Capacitor. On the web, "Watch a sponsor" shows the sponsor card.
Inside the native app it plays a real AdMob rewarded video (falls back to the sponsor card if no ad fills).
Test ad units are built in, so nothing earns money or breaks policy until you swap in your own ids.

## One-time setup (on your Mac)
1. Install Node 20+, Android Studio (Android) and Xcode (iOS).
2. `cd native && npm install`
3. `npx cap add android` and/or `npx cap add ios`
4. Add the AdMob **app id** (test ids below, swap for yours later):
   - Android: `android/app/src/main/AndroidManifest.xml`, inside `<application>`:
     `<meta-data android:name="com.google.android.gms.ads.APPLICATION_ID" android:value="ca-app-pub-3940256099942544~3347511713"/>`
   - iOS: `ios/App/App/Info.plist`: key `GADApplicationIdentifier`, string `ca-app-pub-3940256099942544~1458002511`
     (also add `NSUserTrackingUsageDescription` if you ever turn personalised ads on; the default here is non-personalised for teens)
5. `npm run android` or `npm run ios` opens the project. Press Run on a phone or emulator and tap "Watch a sponsor" to see a test rewarded video.

## Going live (earning money)
1. Make an AdMob account (account owner must be 18+; a parent can own it). Add the app, create a **Rewarded** ad unit for each platform.
2. In `index.html` find `const ADMOB=` and replace the two ids with your real ad unit ids, set `test:false`, replace the test app ids from step 4 with your real ones.
3. Apple Developer ($99/yr) and Google Play Console ($25 once) accounts, then archive and upload (Xcode: Product > Archive; Android Studio: Build > Generate Signed Bundle).
4. Store listing needs a privacy policy URL. Say you use AdMob, set the age rating to include teens, and answer the "ads" and "data safety" questions honestly.

## After every change to the web app
`npm run sync` re-copies the web files into the native projects (run it before building a new release).
