extends SceneTree
const Baseline = preload("feedback_baseline_round11.gd")
const Candidate = preload("feedback_native_round11.gd")
const OldConsumer = preload("feedback_old_round11.gd")
var records: Array = []
var failures: Array = []
func _initialize() -> void: call_deferred("run")
func target(dimensions: Vector2i) -> SubViewport:
	var view := SubViewport.new()
	view.size=dimensions
	view.disable_3d=true
	view.transparent_bg=true
	view.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(view)
	return view
func run() -> void:
	var output := OS.get_environment("BELT_FEEDBACK_OUTPUT")
	DirAccess.make_dir_recursive_absolute(output)
	for pitch in [128,55,32]:
		for orientation in ["portrait","landscape"]:
			var content_size := Vector2(pitch*7,ceili(pitch*7*16.0/9.0)) if orientation=="portrait" else Vector2(pitch*14,pitch*7*16.0/9.0)
			var dimensions := Vector2i(ceili(content_size.x),ceili(content_size.y))
			for camera in [Vector2.ZERO,Vector2(0.12345,0.45678)]:
				for symbol in [{"kind":"clock","progress":-1.0},{"kind":"timer","progress":0.0},{"kind":"timer","progress":0.001},{"kind":"timer","progress":0.1},{"kind":"timer","progress":0.25},{"kind":"timer","progress":0.5},{"kind":"timer","progress":0.75},{"kind":"timer","progress":1.0}]:
					var before := target(dimensions)
					var after := target(dimensions)
					var previous := target(dimensions)
					var baseline: Control=Baseline.new()
					var native: Control=Candidate.new()
					var old: Control=OldConsumer.new()
					before.add_child(baseline)
					after.add_child(native)
					previous.add_child(old)
					for view in [baseline,native,old]:
						view.size=content_size
						view.state={"floor":{"columns":7},"camera":{"x":camera.x,"y":camera.y},"_probe_kind":symbol.kind,"_probe_progress":symbol.progress}
						view.update_layout()
						view.queue_redraw()
					native._native_world_layer.sync()
					old._native_world_layer.sync()
					await process_frame
					await RenderingServer.frame_post_draw
					await process_frame
					await RenderingServer.frame_post_draw
					var name: String="%s-%s-%s-%s-%s" % [pitch,orientation,"aligned" if camera==Vector2.ZERO else "fractional",symbol.kind,str(symbol.progress)]
					var paths: Dictionary={}
					for pair in [["baseline",before],["candidate",after],["old",previous]]:
						paths[pair[0]]=output.path_join(name+"-"+pair[0]+".png")
						assert(pair[1].get_texture().get_image().save_png(paths[pair[0]])==OK)
					var base: Vector2=baseline.cell_base(2,4)
					var center: Vector2=base-Vector2(baseline.cell*.42,baseline.cell*1.25) if symbol.kind=="clock" else base+(Vector2(0,-172)+Vector2(37,-84))*baseline.cell/baseline.art.cell_size
					var radius: float=baseline.cell*(.10 if symbol.kind=="clock" else .115)
					var factor: float=native._native_world_layer.native_view._native_screen_pixel_scale
					var expected: float=1.4 if symbol.kind=="clock" else maxf(1.4,baseline.cell*.032)
					var actual: float=(1.4*factor if symbol.kind=="clock" else maxf(1.4*factor,256.0*.032))*native.cell/256.0
					var old_width: float=(1.4 if symbol.kind=="clock" else maxf(1.4,256.0*.032))*native.cell/256.0
					if absf(actual-expected)>.000001: failures.append(name+" nominal stroke")
					records.append({"name":name,"pitch_requested":pitch,"cell_actual":baseline.cell,"orientation":orientation,"source_control_size":[content_size.x,content_size.y],"viewport_size":[dimensions.x,dimensions.y],"camera":[camera.x,camera.y],"symbol":symbol.kind,"progress":symbol.progress,"center":[center.x,center.y],"radius":radius,"expected_stroke_px":expected,"candidate_stroke_px":actual,"old_stroke_px":old_width,"native_factor":factor,"paths":paths})
					before.queue_free()
					after.queue_free()
					previous.queue_free()
					await process_frame
	var f:=FileAccess.open(output.path_join("feedback-record.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"cases":records,"failures":failures,"godot":Engine.get_version_info(),"method":"Actual GL GPU rendering of original baseline, sealed round10 and corrected round11 _chef_at/_feedback_at; only sprite drawing suppressed. Native helper camera transforms, native256 composition, premultiplied reduction and presentation are exact runtime code. Landscape Controls use fractional logical heights to exercise exact128/55/32 pitches; viewport allocation rounds up, original source-coordinate layout is retained for all three paths."},"  "))
	f.close()
	print("FEEDBACK ",records.size()," cases / failures ",failures)
	quit(0 if failures.is_empty() else 1)
