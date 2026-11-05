extends RefCounted
## The one debug flag behind every cheat (on-screen shortcut buttons and the
## like). On with `--cheats` on the command line, or `"cheats": true` in
## branding.json, which `tools/build_android.py --cheats` sets in a staged APK
## only. Rules never read it: cheats are ordinary commands the UI offers.
static var _enabled = null

static func enabled() -> bool:
	if _enabled == null:
		var branding = JSON.parse_string(FileAccess.get_file_as_string("res://branding.json")) if FileAccess.file_exists("res://branding.json") else null
		_enabled = "--cheats" in OS.get_cmdline_user_args() or (branding is Dictionary and branding.get("cheats", false) == true)
	return _enabled
