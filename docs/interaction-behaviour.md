# Interaction behaviour — 0.7.0

The interface text is German (`lang="de-DE"`), including Settings, HDMI shortcuts, dialogs, errors, status lines and accessible labels. Product and service names (Art Mode, Samsung Home, Dock, Layout, HDMI, app names) and “Shortcut” stay in English. Wallpaper display names come from `app/assets/wallpapers/catalog.js`; the credit register in `SOURCES.json` keeps the original names. The quoted English labels below are the identifiers used in this document, not the displayed text.

## Home

- Dock: Left/Right scrolls the apps without wrapping. Up enters the top-right controls, starting with Art Mode or the last selected control. Left/Right moves between Art Mode, All apps, Sound and Settings. Down or Back returns to the selected app. The clock is at the top left.
- List: Up/Down scrolls the apps without wrapping. Right enters the bottom-right controls, aligned with the clock above. Up/Down moves between Art Mode, All apps, Sound and Settings. Left or Back returns to the selected app. The list fades at both ends as it scrolls.
- OK opens the selected item. Focus alone never launches an app.
- Icons-only apps and controls reveal their names when focused. App presentation and control presentation are independent.
- Back from the app list or Dock opens a choice to stay or open Samsung Home.
- A panel keeps focus within its own controls. Back closes one panel at a time.
- Returning to the running launcher keeps the selected app or panel item. There is no auto-return timer. Held OK and Back keys act once until the key is released.

## Settings and appearance

Settings opens a grouped overview: Background, Layout, Typography, Focus, Apps on Home, HDMI shortcuts and Samsung. OK opens a group. Appearance groups use a two-pane screen with visible choices on the left and the committed Home preview on the right.

| Group | Choices |
| --- | --- |
| Background | Photo, Light, Dark; Wallpaper and Rotation when Photo is active |
| Layout | List or Dock; independent Text, Icons or Both choices for apps and Home controls |
| Typography (Schriften) | Four areas, each with its own font list and size slider |
| Focus | Type or Glass; Soft, Frost or Clear tint material |
| Apps on Home | Membership and arrangement editor |
| HDMI shortcuts | Add, edit and delete named input shortcuts |
| Samsung | Samsung Home, TV settings and Inputs |

Up/Down moves between rows. Left/Right moves between choices in a horizontal row. Focus alone changes neither the preview nor saved preferences in these appearance groups. Wallpaper has its own temporary photo preview, described below. OK applies the focused value. A checkmark identifies the applied value; the filled plate identifies remote focus. Applying the current value does not write again.

Material applies to a photographic Dock, or Glass focus on a photographic List. Inactive material choices remain visible with an explanation and are skipped during navigation. Their stored value is retained. Wallpaper and rotation are also inactive on flat backgrounds.

A font or photo change applies only after its resources are ready and storage succeeds. A load or storage failure keeps the previous appearance and checkmark, with a Try again action. Back cancels a pending change, leaves the group and keeps completed changes. Late load callbacks cannot apply a cancelled choice. There is no Save button. Returning to a group restores its last choice focus; returning to Settings restores its category focus. Rotation is nested within Background, and Back returns to its Rotation row.

Typography (Schriften) has four independent areas. Each opens a font list (Standard, Orbitron, Roboto) and a size slider:

| Area | Covers | Sizes |
| --- | --- | --- |
| Uhrzeit und Datum | Home clock and the date below it (the date stays smaller) | 80–160 % |
| App- und Shortcut-Namen | App and HDMI shortcut names on Home, in the Home editor, All apps and the shortcut preview | 80–120 % |
| Einstellungs- und Menütexte | Settings titles, groups, choices, section labels, Home controls, buttons, dialog titles | 80–120 % |
| Sonstige Texte | Descriptions, hints, help, status and error lines, dialog text | 80–130 % |

Standard is the bundled Manrope; at Standard and 100 % every text, icon and app mark keeps its position, size and font from `de05deb` (checked by `npm run check:typography`), apart from the new date and the renamed Schriften group. The time keeps its position and size; the date is centred below it and stays within the width of the time. If the date would be wider, only the date's font size is reduced to fit. The check runs with every Home render but compares only state and text (fonts, sizes, time, date, layout); the elements are measured only when one of these changes, and otherwise no DOM access or layout read takes place. Icons beside text keep their designed Manrope positions; another font moves them only by the difference between its optical centre and Manrope's. Orbitron uses its lightest upstream weight (400). A font change follows the other appearance choices: focus alone changes nothing, OK loads the font and applies and saves it, Back cancels a font that is still loading, and a failed load keeps the previous font with Try again. Left/Right on the slider steps the size by 10 % and saves it immediately; OK on the slider does nothing. While a font loads, the slider is dimmed, its keys wait and the hint line says so. Each font is listed in its own typeface. The right column shows the area's real text at its actual size (the current time and date, the first Home names, menu labels or a hint) below the live Home preview, and the settings themselves use the menu and text areas as soon as they change.

Preferences store `tfClock`, `tfNames`, `tfMenu`, `tfText` (font) and `tsClock`, `tsNames`, `tsMenu`, `tsText` (percent) in the existing look. The earlier single Home font seeds the clock and names areas; menu and text start at Standard, and all sizes at 100 %. An earlier optional font (Geist, Newsreader or a private Pangram face) stays listed only in an area that already uses it. A saved font that cannot load at startup is shown in Standard for that session. Only the display changes: the saved choice stays in the preferences, later saves of any other setting keep it, and the area says that Standard is shown; OK on that font tries to load it again. A known font that this build does not include, such as a private Pangram, Mori or Montreal face whose files are missing, is treated the same way: it stays saved (also in `look.font` and the copy below), the area shows it as applied but not selectable and says that it is not included in this version, and Standard is shown until a build with the font runs again. Choosing another font for that area replaces it deliberately. Unknown or invalid font IDs fall back to Standard, or for clock and names to the earlier Home font, and invalid sizes to 100 %. For a return to an earlier version, `look.font` is still written from the names area (Orbitron and Roboto as Manrope, which the earlier version knows), and all eight values are also kept under `cleanframe.typography.v1`, which earlier versions neither read nor remove. After a later update they are restored if `look.font` still has the value written here; a font changed in the earlier version wins and seeds the clock and names areas as in the first migration. In the normal rollback, where the font is not changed in the earlier version, all four areas and sizes are restored. Known limitation, deliberately accepted: the earlier version stores no record of changes, so it cannot show that the font was changed in between when the final value equals the original one (for example Geist → Newsreader → Geist, or Manrope via another font back to Manrope while the names area used Orbitron or Roboto). In this rare case the separate copy restores the newer individual areas, for example a Roboto clock, although the last deliberate choice in the earlier version was Geist for the clock, names and Home controls. This affects only the way back through an earlier version. This transition can be removed once a return to versions before the typography settings is no longer supported. App names step down to their reduced size and then end in an ellipsis within the designed widths; Settings columns and the overview scroll to keep focus visible at larger sizes. If the baseline font is slow or missing, Home remains usable with a local fallback and can recover when the font loads.

## Streaming apps

The nine default apps keep their known native IDs. Other installed consumer apps can also be added to Home. Launching uses the public `tizen.application.launch` API with the app's native ID. Missing apps and denied launches produce a real error. No web player, placeholder success page or account credential is embedded.

## All apps

The panel reads `tizen.application.getAppsInfo` on entry and shows the filtered consumer apps alphabetically. Samsung's visibility flag alone also exposes system utilities, so EP packages, background services, ad players, account utilities, placeholders and duplicates are omitted. Known brands use bundled marks. Other apps use their local installed icon, with initials as a fallback.

The five-column grid scrolls with remote focus. OK launches an app; its On Home badge shows membership. Up from the first row reaches Apps on Home, which opens the editor. An API failure shows a retry and keeps saved Home choices. Browser previews report that installed-app discovery and launching require the TV.

## Apps on Home

Open the editor from Settings or All apps. On Home shows the current order on the left. Not on Home shows Recently removed first, followed by other installed apps on the right. Home holds one to nine apps.

- Reorder: OK on an app name picks it up. Up/Down moves it. OK places it and saves the order. Back puts an unplaced app back without saving that move.
- Remove: Right from an app name reaches Remove from Home. OK saves the removal and moves focus to the same app in Recently removed. The app stays installed.
- Add: OK on an app in Not on Home adds it and saves. A recently removed app returns to its previous position within the editing session; another app is added at the end. Focus follows the app to its Remove from Home control, so another OK can reverse the addition.
- Undo reverses a completed addition, removal or reorder from the current editing session. Done or Back closes the editor and keeps completed changes. Undo history ends when the editor closes.

Removing the last Home app or adding a tenth app is prevented. A failed storage write keeps the committed choices and order, with a retry message. Saved native app IDs and names survive a restart or a failed catalogue refresh.

## Art Mode and Samsung screens

Art Mode sends an application control to the installed `org.tizen.art-app`, with `mode=fullscreen` and `requester=mobile`. This aims to enter native Art Mode with its current artwork, without toggling power or changing the selected artwork.

This mode comes from [research on Samsung's Art app](https://github.com/TheFab21/ha-samsungtv-smart/blob/master/notes/QN55LS03FAFXZA/ART_MODE_DECOMPILED.md), on another Tizen 9 Frame model. It is an internal Samsung contract, not a documented public Art API. Its visible behaviour on this exact firmware must be confirmed on the TV.

Samsung Home explicitly launches the original `com.samsung.tv.csfs` app, independently of the new Home assignment. The earlier `com.samsung.tv.coba.newhome` component did not open Smart Hub visibly and is no longer the escape target. TV settings still uses `com.samsung.tv.coba.setting`. Exact on-device destinations are recorded in docs/tv-status.md; launch callbacks alone are not visual proof. There is no blind power-key fallback.

All calls have bounded response handling. A failure leaves CleanFrame usable. No simulated device success views remain. Browser validation cannot confirm the visible Samsung destination.

Installed-app discovery allows up to 20 seconds for large TV catalogues; launch controls retain an 8-second limit. Opening All apps or the editor refreshes the catalogue while retaining saved Home choices. No discovery polling runs during hidden startup.

## Sound output

The Sound control on Home opens Samsung's TV settings through the same `com.samsung.tv.coba.setting` launch as Settings → Samsung → TV settings. The owner chooses TV speaker, Bluetooth or another output there. The public TV APIs cannot read or switch the audio output device: `tvaudiocontrol.getOutputMode()` reports the audio format, and `avinfo.setSubAmpMode()` is limited to Hotel TVs. Sound therefore shows no active-output mark and changes no setting itself. A failed launch shows an error. Whether the settings screen opens on a particular TV must be confirmed on that TV.

## HDMI inputs

Settings → Samsung → Inputs opens the HDMI chooser. The adapter reads the TV’s actual connected and disconnected source records, including sleeping devices that may be listed as disconnected. It does not guess a universal port count or add an Inputs control to Home. Missing APIs, denied access and discovery failure produce an unavailable/error state rather than invented ports. The active source comes from the synchronous `tvwindow.getSource()` return value.

Up/Down selects an input. OK requests that exact source; Back returns to Samsung Settings. Retry after a failed load rereads the available sources. A routing error remains an error, and a failed handoff leaves the launcher usable. Timed-out or cancelled requests cannot start a later routing or viewer action; a native request already sent to the TV may itself be uncancellable.

Selecting a source, opening Samsung’s viewer, seeing the expected HDMI picture and waking a CEC device are separate results.

## HDMI shortcuts

Settings → HDMI shortcuts lists saved shortcuts and Add shortcut. A shortcut has an HDMI port, a name of up to 40 characters and an image. Up to twelve can be saved.

- Input offers the ports reported by `FrameDevice.sources()`, including sleeping devices. A new shortcut starts on the first connected unused port. A saved port the TV no longer reports stays selectable with a warning; no port is invented. Without the source API, Add stays unavailable.
- Image offers bundled marks: PlayStation, a handheld console, a game controller, Apple TV, a streaming stick, a disc player, PC, receiver and a generic HDMI connector. Until a name is typed, the image suggests one (PlayStation 5, Nintendo Switch 2, Xbox, Apple TV, Fire TV, Blu-ray player, PC, Receiver, or HDMI and the port number).
- Name opens a real text field. Samsung’s on-screen keyboard is expected to open when it takes focus. While typing, the launcher’s key map is suspended, so Backspace and the arrows edit the text. Done (key 65376) or Enter keeps the name; Cancel (65385), Escape or Back restores the previous name. A held OK opens the field once. An empty name is refused and the previous name kept. Names are always shown as text.
- Add or Save writes the preferences once. A storage failure keeps the editor and the previous saved state. Delete asks for confirmation and removes the shortcut from Home and recent apps; the only Home item cannot be deleted.

A shortcut is a Home item. It counts towards the nine Home places, appears in Dock and List with its image and name, and is arranged, removed or added again in Apps on Home. A new shortcut joins the end of Home, or Not on Home when Home is full. OK on its tile uses the same bounded `FrameDevice.setSource()` route as Inputs: the port is checked against a fresh source list, then Samsung’s viewer opens. A port that is no longer reported, a routing failure or a timeout shows an error.

Shortcuts are stored as `inputs` in `cleanframe.home.v1`. Unknown or malformed entries are dropped on load and an unknown image falls back to the HDMI mark. Earlier preferences without `inputs` load unchanged. A shortcut stores the port number only: the public source API exposes no device identity, so moving a cable to another port is not detected. The on-screen keyboard, the visible HDMI picture and CEC wake must be confirmed on each TV. The portable implementation does not import firmware-specific viewer payloads or claim to wake a sleeping device. No input discovery or polling runs during hidden startup.

## Preferences and wallpaper

The launcher stores appearance, Home order, recently removed apps, the last launched Home app, wallpaper and rotation locally. List and Dock share these preferences. The existing `cleanframe.home.v1` key is retained, with a fallback read from `cleanframe.shore.v1`. Legacy List maps to Dark + List + Type; Glass Dock and Glass Grid map to Photo + Dock + Glass. App order, wallpaper, rotation and the last Home app are preserved.

The gallery contains 15 bundled wallpapers. Settings → Background → Wallpaper keeps the two-pane Settings frame. Up/Down browses a vertical thumbnail list without wrapping; the right-hand Home preview shows the candidate while the surrounding Settings backdrop stays on the applied photo. OK applies the focused photo and stays in Wallpaper. The tick marks the applied photo and preview status distinguishes unsaved browsing. Back restores the latest applied photo, cancels pending loading and returns to Background’s Wallpaper row. Photo and material assets change as one complete bundle; a failed load restores the applied preview and offers retry. Preview loading waits briefly for remote focus to settle. OK during loading queues application for that photo; another browse move or Back cancels it. Browsing never saves, and repeated OK on the applied photo does not write again.

Settings → Background → Rotation offers Fixed, Each time Home opens, Every 5 minutes, Every 15 minutes and Every hour. Each time Home opens advances once when the launcher loads; a return to the already-running launcher does not advance it. Timed rotation counts only visible Photo Home time in either List or Dock. Panels, flat backgrounds and time spent in other apps pause the cycle. Changing the photo or rotation mode starts a new interval.

Launcher wallpaper is separate from native Art Mode. Runtime photos, materials and available fonts are local assets; they do not require the Mac or a network download.

## Sources

- [Samsung Application API](https://developer.samsung.com/smarttv/develop/api-references/tizen-web-device-api-references/application-api.html): installed-app discovery and application control.
- [Samsung application termination guide](https://developer.samsung.com/smarttv/develop/guides/fundamentals/terminating-applications.html): exiting is not treated as a deterministic Samsung Home route.

The native Home operation and startup configuration from 19 October remain separate from this app update. Home from Netflix was confirmed for that configuration; power-on after Netflix remains provisional. Streaming apps retain their own Back navigation. Netflix did not exit on repeated Back in the observed test, so there was no app-exit destination to verify. No global Back interception or key-filter hook was installed. See [TV status](tv-status.md) for device evidence; this behaviour specification is not an installation or visual-verification record for 0.6.0.

## Clock and rendering

Both layouts show the TV's local time in German 24-hour format with two-digit hours (09:05, 13:51), without seconds. The local date follows directly below in dd.mm.yyyy format (18.11.2026), smaller than the time and in the same font. Both update at the minute boundary, including midnight, and on return to the launcher.

Photographic materials and blurred panel backgrounds are generated before packaging and stay aligned with the full-screen image. Photo colour and contrast metadata are also prepared offline. Navigation does not sample image pixels, run an optics engine or apply live backdrop blur. Flat backgrounds use matching light or dark panel colours. Focus feedback uses transforms and opacity; reduced motion removes animated scaling and movement while retaining opacity feedback.

Hidden prelaunch can install a fully loaded wallpaper bundle without waiting for an animation frame. A valid loaded image remains usable if detached-image decoding rejects. A failed startup bundle retries when the launcher becomes visible; an active wallpaper preview keeps its candidate. Font recovery clears fallback measurements and cached markup. This readiness fallback uses a completed load and nonzero image dimensions; it does not prove a TV has painted the image, and an accepted bundle is not automatically decoded again on return. These paths have browser regression coverage; physical cold-boot behaviour still needs owner observation.
