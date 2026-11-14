extends SceneTree
## Issue #76: store each reef chunk's fair lines in its document
## (`chunk.reef`), as reef.gd describes. Run after editing a reef chunk or the
## reef/handling balance in content/expedition.json:
##   godot --headless --path . --script res://tools/reef_tables.gd
## Pass `-- --check` to report stale tables without writing (exit code 1).

const Route = preload("res://scripts/expedition/route.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
const Reef = preload("res://scripts/expedition/reef.gd")

func _init() -> void:
	var check := "--check" in OS.get_cmdline_user_args()
	var rules := Book.definition()
	var stale := 0
	for file in DirAccess.get_files_at(Route.CHUNK_DIR):
		if not file.ends_with(".json"): continue
		var path := Route.CHUNK_DIR.path_join(file)
		var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
		var chunk := Route.chunk_from_map(doc, file.get_basename())
		if chunk.kind != "creature" or str(Book.species(str(chunk.creature)).attack) != "reef": continue
		var problems := Route.validate_chunk(chunk)
		if not problems.is_empty():
			printerr("%s: %s" % [chunk.id, "; ".join(problems)]); stale += 1; continue
		var current = doc.chunk.get("reef")
		if current is Dictionary and str(current.get("key")) == Reef.key(chunk.rows, rules):
			print("%s: up to date" % chunk.id); continue
		stale += 1
		if check:
			printerr("%s: reef table is stale" % chunk.id); continue
		var started := Time.get_ticks_msec()
		var table := Reef.analyze(chunk, rules, Book._collides)
		doc.chunk.reef = table
		var out := FileAccess.open(path, FileAccess.WRITE)
		out.store_string(JSON.stringify(doc, "  ", false) + "\n")
		print("%s: %s, %d fair lines, %d rejected (%d ms)" % [chunk.id, "accepted" if table.accepted else "REJECTED " + "; ".join(table.problems),
			table.lines.size(), table.rejected, Time.get_ticks_msec() - started])
	quit(1 if check and stale > 0 else 0)
