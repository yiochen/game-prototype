extends SceneTree
## Issue #25: store each creature chunk's fair-strike table in its document
## (`chunk.discharge`), as discharge.gd describes. Run after editing a creature
## chunk or the discharge/handling balance in content/expedition.json:
##   godot --headless --path . --script res://tools/discharge_tables.gd
## Pass `-- --check` to report stale tables without writing (exit code 1).

const Route = preload("res://scripts/expedition/route.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
const Discharge = preload("res://scripts/expedition/discharge.gd")

func _init() -> void:
	var check := "--check" in OS.get_cmdline_user_args()
	var rules := Book.definition()
	var stale := 0
	for file in DirAccess.get_files_at(Route.CHUNK_DIR):
		if not file.ends_with(".json"): continue
		var path := Route.CHUNK_DIR.path_join(file)
		var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
		var chunk := Route.chunk_from_map(doc, file.get_basename())
		# Reef chunks (#76) keep fair lines instead: tools/reef_tables.gd.
		if chunk.kind != "creature" or str(Book.species(str(chunk.creature)).attack) != "discharge": continue
		var problems := Route.validate_chunk(chunk)
		if not problems.is_empty():
			printerr("%s: %s" % [chunk.id, "; ".join(problems)]); stale += 1; continue
		var current = doc.chunk.get("discharge")
		if current is Dictionary and str(current.get("key")) == Discharge.key(chunk.rows, chunk.attack_rows, rules):
			print("%s: up to date" % chunk.id); continue
		stale += 1
		if check:
			printerr("%s: discharge table is stale" % chunk.id); continue
		var started := Time.get_ticks_msec()
		var rows: Array = chunk.rows
		var reach := float(rules.ship_radius)
		var table := Discharge.analyze(rows, chunk.attack_rows, rules, func(x: float, y: float) -> bool: return Book._collides(rows, x, y, reach))
		# Only the fair choices ship; the unfair ones are kept for review counts.
		var stored := {"key": table.key, "accepted": table.accepted, "problems": table.problems,
			"strikes": table.strikes.map(func(s): return {"row": s.row, "fair": s.fair, "unfair": s.unfair.size()})}
		doc.chunk.discharge = stored
		var out := FileAccess.open(path, FileAccess.WRITE)
		out.store_string(JSON.stringify(doc, "  ", false) + "\n")
		print("%s: %s, %d strike rows, fair strips %s (%d ms)" % [chunk.id, "accepted" if table.accepted else "REJECTED " + "; ".join(table.problems),
			table.strikes.size(), ",".join(table.strikes.map(func(s): return str(s.fair.size()))), Time.get_ticks_msec() - started])
	quit(1 if check and stale > 0 else 0)
