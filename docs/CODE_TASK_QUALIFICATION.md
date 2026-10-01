# Cross-Product Code Task Qualification

**Date:** 2026-08-12

**Purpose:** record whether each proposed maintenance task has a real local test contract and a safe runner path before it can become an evaluation gate. Qualification does not train a model, mutate a source file, or promote an adapter.

## Runner policy

- A live repository is never mutated for evaluation.
- Build/test products go to a dedicated temporary Derived Data path or SwiftPM build location.
- A task becomes **executable-qualified** only after its original source and original test pass with a documented command.
- A task remains **discovered** if its source/test contract is verified but its isolated runner has not yet been proven.
- No discovered task can contribute a simulated pass or promotion credit.

## Qualification matrix

| ID | Product | Source/test contract | Runner | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| CAM-01 | Camera App | `basic/Models/Ladders.swift` / `basicTests/StackPolicyTests.swift` | Xcode scheme `basic` | Executable-qualified | The Xcode result bundle records 2 passing `StackPolicyTests` on the fixed iOS simulator. The platform warning was non-fatal. |
| CAM-02 | Tanzaku | `Tanzaku/Domain/PreviewGeometry.swift` / `TanzakuTests/GeometryPolicyTests.swift` | Xcode scheme `Tanzaku` | Executable-qualified | `PreviewGeometryTests` passed on the fixed iOS simulator with temporary Derived Data. |
| PHOTO-01 | Kineto | `Kineto/Domain/EraMatrix.swift` / `KinetoTests/EraMatrixTests.swift` | Xcode scheme `Kineto` | Executable-qualified | `EraMatrixTests` passed on the fixed iOS simulator with temporary Derived Data. |
| PHOTO-02 | SixTwelve PhotoLab | `Sources/PLCore/PLDocument.swift` / `Tests/DocumentModelTests.swift` | Xcode scheme `SixTwelvePhotoLab_macOS` | Executable-qualified | `testChecksumIsStableAndKnown` passed on macOS with temporary Derived Data. |
| PHOTO-03 | Photo editing app | `whistler/Processing/Recipes/RecipeLibrary.swift` / `whistlerTests/RecipeParityTests.swift` | Xcode scheme `whistler` | Executable-qualified | The Xcode result bundle records 1 passing `RecipeParityTests` test on the fixed iOS simulator. The platform warning was non-fatal. |
| LUMEN-01 | Lumen | `Lumen/Services/CommandPlanner.swift` / `LumenTests/LumenTests.swift` | Xcode macOS `Lumen` scheme | Executable-qualified | `testCommandParserUsesTheRequestedAmount` passed with temporary Derived Data. |
| LUMEN-02 | Lumen | `Lumen/Model/HistoryTimeline.swift` / `LumenTests/LumenTests.swift` | Xcode macOS `Lumen` scheme | Executable-qualified | `testHistoryTimelineDropsRedoBranch` passed with temporary Derived Data. |
| DICT-01 | Dictionary | `DictionaryApp/Theme/LemmaTheme.swift` / `DictionaryAppTests/LemmaThemeTests.swift` | Xcode scheme `DictionaryApp` | Executable-qualified | `testSerifScaleIsMonotonic` passed on the fixed iOS simulator with temporary Derived Data. |
| QURAN-01 | Mishkat Quran | `Packages/MishkatKit/Sources/QuranDomain/Identifiers/VerseReference.swift` / `Packages/MishkatKit/Tests/QuranDomainTests/VerseReferenceTests.swift` | SwiftPM `MishkatKit` | Executable-qualified | `swift test --filter VerseReferenceTests` passed: 9 tests in 2 suites. |
| QURAN-02 | Mishkat Quran | `QuranDomain/Audio/PlaybackState.swift` / `QuranDomainTests/RepeatSettingsTests.swift` | SwiftPM `MishkatKit` | Executable-qualified | `RepeatCountTests` passed: 3 tests in 1 suite. |
| NG-01 | NauticGrid | `lib/operator/entry-href.ts` / `lib/operator/entry-href.test.ts` | local Vitest | Executable-qualified | Existing temporary-copy fixture; baseline Code base result 0/1. |
| NG-03 | NauticGrid | `lib/operator/priority.ts` / `lib/operator/priority.test.ts` | local Vitest | Executable-qualified | Existing temporary-copy fixture; baseline Code base result 0/1. |

## Verified commands

```bash
# Quran domain — passed on 2026-08-12
swift test --package-path ../mishkat-quran-app/Packages/MishkatKit --filter VerseReferenceTests

# Lumen command parser — passed on 2026-08-12
xcodebuild test -project ../lumen-app/Lumen.xcodeproj -scheme Lumen \
  -destination 'platform=macOS' \
  -derivedDataPath /tmp/sixtwelve-lumen-qualification \
  -only-testing:LumenTests/LumenTests/testCommandParserUsesTheRequestedAmount

# SixTwelve PhotoLab document model — passed on 2026-08-12
xcodebuild test -project ../sixtwelve-photolab-app/SixTwelvePhotoLab.xcodeproj \
  -scheme SixTwelvePhotoLab_macOS -destination 'platform=macOS,arch=arm64' \
  -derivedDataPath /tmp/sixtwelve-photolab-qualification \
  -only-testing:SixTwelvePhotoLabTests/DocumentModelTests/testChecksumIsStableAndKnown

# Lumen history branch behavior — passed on 2026-08-12
xcodebuild test -project ../lumen-app/Lumen.xcodeproj -scheme Lumen \
  -destination 'platform=macOS,arch=arm64' \
  -derivedDataPath /tmp/sixtwelve-lumen-qualification \
  -only-testing:LumenTests/LumenTests/testHistoryTimelineDropsRedoBranch

# Quran repeat policy — passed on 2026-08-12
swift test --package-path ../mishkat-quran-app/Packages/MishkatKit --filter RepeatCountTests

# Camera App stack policy — passed on 2026-08-12
xcodebuild test -project ../camera-app/basic.xcodeproj -scheme basic \
  -destination 'platform=iOS Simulator,id=2404F9B1-282A-4E23-8277-F3B547A83C87' \
  -derivedDataPath /tmp/sixtwelve-camera-qualification \
  -only-testing:basicTests/StackPolicyTests

# Photo editing recipe parity — passed on 2026-08-12
xcodebuild test -project ../photo-editing-app/whistler.xcodeproj -scheme whistler \
  -destination 'platform=iOS Simulator,id=2404F9B1-282A-4E23-8277-F3B547A83C87' \
  -derivedDataPath /tmp/sixtwelve-whistler-qualification \
  -only-testing:whistlerTests/RecipeParityTests
```

## Current qualification result

All twelve tasks have real executable paths demonstrated: Camera App stack policy, Tanzaku geometry, Kineto matrix safety, SixTwelve PhotoLab document integrity, photo-editing recipe parity, Lumen command parsing and history safety, Dictionary Dynamic Type behavior, Mishkat Quran reference parsing and repeat policy, and two NauticGrid TypeScript policy tasks. The two iOS schemes emit an `IDERunDestination` platform warning, but their Xcode result bundles prove the selected tests passed; it is non-fatal for these contracts.

## Next implementation boundary

After approval of the cross-product task set, implement a task manifest and temporary-copy runner for all twelve qualified tasks. Do not widen the evaluation suite merely to inflate coverage.
