class_name SaveStore
extends RefCounted
## File persistence only. GameSession owns the snapshot schema and every reward.
## Loading never advances time, replays commands, or grants offline income.

const FORMAT := "sushi-loop-session"
## Version 2 holds the store-based session. Older files are unreleased
## prototype data and are discarded on load, so the game starts fresh.
const FORMAT_VERSION := 2
const MAX_SAVE_BYTES := 16 * 1024 * 1024

var last_error := ""
var source := "none"
var _directory: String
var _validator: Callable = Callable()
## Called on the writing thread with each session before it is written.
## Tests use it to hold a write in progress; the game leaves it unset.
var before_write: Callable = Callable()
var _preserve_failed_load := false
var _validated_payloads: Dictionary = {}
var _autosave_thread: Thread
var _queued_autosave: Dictionary = {}
var _autosave_result: Dictionary = {}

func _init(directory: String = "user://") -> void:
	_directory = directory.trim_suffix("/")
	if directory == "user://":
		_directory = "user://"

func load_session(validator: Callable = Callable()) -> Dictionary:
	finish_autosave()
	_discard_outdated()
	# Optional pure domain validation allows schema-invalid primary files to use
	# a playable backup while keeping this storage class independent of rules.
	if validator.is_valid():
		_validator = validator
		_validated_payloads.clear()
	last_error = ""
	source = "none"
	_preserve_failed_load = false
	for candidate in ["primary", "backup"]:
		var loaded := _read_valid(_path(candidate))
		if not loaded.is_empty():
			source = candidate
			return loaded.data.duplicate(true)
	if FileAccess.file_exists(_path("primary")) or FileAccess.file_exists(_path("backup")):
		last_error = "No valid saved session was found."
		_preserve_failed_load = true
	return {}

func save_session(session_data: Dictionary) -> bool:
	# A player action or suspension supersedes queued simulation snapshots. Join
	# the sole writer before committing, so older work cannot overwrite it later.
	_queued_autosave.clear()
	_join_autosave()
	return _save_session(session_data)

func request_autosave(session_data: Dictionary) -> void:
	# The caller may continue simulating immediately. One worker owns the store;
	# while it writes, retain only the newest independently owned snapshot.
	_queued_autosave = session_data.duplicate(true)
	if _autosave_thread == null: _start_autosave()

func poll_autosave() -> Dictionary:
	if _autosave_thread == null: return _join_autosave()
	if _autosave_thread.is_alive(): return {}
	var result := _join_autosave()
	if not _queued_autosave.is_empty(): _start_autosave()
	return result

func finish_autosave() -> bool:
	var result := _join_autosave()
	if not _queued_autosave.is_empty():
		var latest := _queued_autosave
		_queued_autosave = {}
		return _save_session(latest)
	return result.get("ok", true)

func _start_autosave() -> void:
	var data := _queued_autosave
	_queued_autosave = {}
	_autosave_thread = Thread.new()
	if _autosave_thread.start(_save_session.bind(data), Thread.PRIORITY_LOW) != OK:
		_autosave_thread = null
		# Keep the existing synchronous persistence if a device cannot start a worker.
		var success := _save_session(data)
		_autosave_result = {"ok":success,"error":"" if success else last_error}

func _join_autosave() -> Dictionary:
	if _autosave_thread == null:
		var result := _autosave_result
		_autosave_result = {}
		return result
	var success: bool = _autosave_thread.wait_to_finish()
	_autosave_thread = null
	return {"ok":success,"error":"" if success else last_error}

func _save_session(session_data: Dictionary) -> bool:
	last_error = ""
	if _preserve_failed_load:
		return _fail("The existing save files are preserved because they could not be restored.")
	if session_data.is_empty():
		return _fail("An empty session cannot replace a saved game.")
	if before_write.is_valid(): before_write.call(session_data)
	# Game rules are checked when a save is loaded, never on the way out: a
	# rejected save would block every later save (the 0.16.1 lock-up). Writing
	# only proves the file reads back to exactly these bytes.
	var payload := JSON.stringify(session_data, "", true, true)
	if not JSON.parse_string(payload) is Dictionary:
		return _fail("The session could not be serialized.")
	# Hash the stored bytes, not a re-serialized dictionary with float conversions.
	var serialized := JSON.stringify({
		"format": FORMAT,
		"version": FORMAT_VERSION,
		"payload": payload,
		"sha256": payload.sha256_text(),
	})
	if serialized.to_utf8_buffer().size() > MAX_SAVE_BYTES:
		return _fail("The saved session is too large.")
	var absolute_directory := ProjectSettings.globalize_path(_directory)
	var mkdir_error := DirAccess.make_dir_recursive_absolute(absolute_directory)
	if mkdir_error != OK:
		return _fail("Could not create the save directory (%s)." % mkdir_error)
	if not _write_checked(_path("pending"), serialized):
		return false
	# The previous generation becomes the backup only if it passes the game's
	# rules (cached per file); otherwise the existing backup stays. This never
	# blocks the new write.
	var previous := _read_valid(_path("primary"))
	# Never replace a valid backup with a damaged primary. A first save creates
	# its recovery copy before promotion, so interruption always leaves a valid file.
	if not previous.is_empty() or _read_valid(_path("backup")).is_empty():
		var backup_text: String = previous.get("raw", serialized)
		if not _write_checked(_path("backup_pending"), backup_text):
			return false
		if not _promote(_path("backup_pending"), _path("backup")):
			return false
	if not _promote(_path("pending"), _path("primary")):
		return false
	source = "primary"
	return true

func clear_session() -> bool:
	_queued_autosave.clear()
	_join_autosave()
	last_error = ""
	for candidate in ["primary", "backup", "pending", "backup_pending"]:
		var path := _path(candidate)
		if FileAccess.file_exists(path):
			var error := DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
			if error != OK:
				return _fail("Could not clear the saved session (%s)." % error)
	source = "none"
	_preserve_failed_load = false
	_validated_payloads.clear()
	return true

func _discard_outdated() -> void:
	for kind in ["primary", "backup", "pending", "backup_pending"]:
		var path := _path(kind)
		if not FileAccess.file_exists(path): continue
		var parser := JSON.new()
		if parser.parse(FileAccess.get_file_as_string(path)) != OK: continue
		var envelope: Variant = parser.data
		var version: Variant = envelope.get("version") if envelope is Dictionary and envelope.get("format") == FORMAT else null
		if (version is int or version is float) and int(version) < FORMAT_VERSION:
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))

func _path(kind: String) -> String:
	var filenames := {
		"primary": "session.json",
		"backup": "session.backup.json",
		"pending": "session.pending.json",
		"backup_pending": "session.backup.pending.json",
	}
	return _directory.path_join(filenames[kind])

## A checksum-verified save; with `domain`, it must also pass the game's
## validator (loading, and choosing what to keep as the backup). Verifying a
## fresh write checks only the checksum.
func _read_valid(path: String, domain := true) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	if file.get_length() > MAX_SAVE_BYTES:
		file.close()
		return {}
	var raw := file.get_as_text()
	file.close()
	var parser := JSON.new()
	if parser.parse(raw) != OK or not parser.data is Dictionary:
		return {}
	var envelope: Dictionary = parser.data
	if envelope.get("format") != FORMAT or envelope.get("version") != FORMAT_VERSION:
		return {}
	var payload: Variant = envelope.get("payload")
	if not payload is String or envelope.get("sha256") != payload.sha256_text():
		return {}
	if parser.parse(payload) != OK or not parser.data is Dictionary or parser.data.is_empty():
		return {}
	if domain and _validator.is_valid() and not _validated_payloads.has(envelope.sha256):
		if not _validator.call(parser.data): return {}
		# Domain validation is pure and belongs to these exact verified bytes.
		# Atomic writes re-read pending, primary and backup files; do not rebuild
		# the same restaurant repeatedly after each successful checksum check.
		_validated_payloads[envelope.sha256] = true
		if _validated_payloads.size() > 4: _validated_payloads.erase(_validated_payloads.keys()[0])
	return {"data": parser.data, "raw": raw}

func _write_checked(path: String, text: String) -> bool:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return _fail("Could not write the saved session (%s)." % FileAccess.get_open_error())
	file.store_string(text)
	file.flush()
	var write_error := file.get_error()
	file.close()
	if write_error != OK or _read_valid(path, false).is_empty():
		return _fail("Saved session verification failed (%s)." % write_error)
	return true

func _promote(from_path: String, to_path: String) -> bool:
	var error := DirAccess.rename_absolute(ProjectSettings.globalize_path(from_path), ProjectSettings.globalize_path(to_path))
	if error != OK:
		return _fail("Could not commit the saved session (%s)." % error)
	return true

func _fail(message: String) -> bool:
	last_error = message
	return false
