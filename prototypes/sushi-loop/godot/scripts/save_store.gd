extends RefCounted

const PATH := "user://harbor_save.json"
const BACKUP := "user://harbor_save.backup.json"

static func read_save() -> Dictionary:
	for path in [PATH, BACKUP]:
		if FileAccess.file_exists(path):
			var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
			if parsed is Dictionary and parsed.get("version", 0) == 1 and parsed.get("restaurant") is Dictionary:
				return parsed
	return {}

static func write_save(data: Dictionary) -> bool:
	var temporary := PATH + ".tmp"
	var f := FileAccess.open(temporary, FileAccess.WRITE)
	if f == null: return false
	f.store_string(JSON.stringify(data))
	f.flush()
	f.close()
	if FileAccess.file_exists(PATH):
		DirAccess.copy_absolute(PATH, BACKUP)
	return DirAccess.rename_absolute(temporary, PATH) == OK
