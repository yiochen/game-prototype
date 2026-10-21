# Night sky and camera clearance

The user requested a quiet top strip for hole-punch cameras, with the complete HUD below it and allowed to overlap the shingles. The room still fills both phone side edges.

The sky is the complete built-in ImageGen output retained at `assets/restaurant-backdrop/night-sky/`, with its exact prompt and SHA-256. The runtime copy is identical. The renderer uniformly crops it to a fixed screen-space strip; room panning cannot move world art or selection into this strip.

The minimum strip is 80 logical units at a 720-unit scene width. Hardware safe-area/cutout bounds can enlarge it, plus a 12-unit clearance. Coins, Editing, Live and Shop use the remaining content area. The bottom rail and controls retain their positions. The reserved three world rows, furniture, economy and save data are unchanged by this view-only clearance.

Mobile display pixels are converted through the inverse viewport transform. [Godot DisplayServer](https://docs.godotengine.org/en/stable/classes/class_displayserver.html#class-displayserver-method-get-display-safe-area) supplies the reported safe area and Android cutout rectangles. Desktop captures use the minimum strip and a simulated larger top clearance. No physical-device installation was performed.

The full native suite passes (13 suites / 2,516 checks), and the expanded native app suite passes all 196 checks at 390×844, including six additional physical/logical conversion, cutout, HUD, input and save invariants. `phone/` and `landscape/` contain actual native renders. Build and artifact audits verify the original signer, stable Restaurant Editor package, nondebuggable release, runtime hashes and the new sky resource in the APK.

[Verified Google Drive APK](https://drive.google.com/file/d/1XrcG8ipY_I4ibPdI3-qsVC7-Jk7nvYwi/view?usp=drivesdk). Version 0.4.11 / code 51; package `com.yiochen.sushilooptickets.review12`; original release signer. Drive readback matches local size and MD5; existing sharing is unchanged. Install over the earlier Restaurant Editor test app.
