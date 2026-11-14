class_name RestaurantAudio
extends Node
## Presentation only: audio never reads or advances the game session.

const AUDIO_PATH := "res://assets/audio/"
const VOICE_COUNT := 6
const COOLDOWN_MS := {"click": 75, "cook": 170, "load": 100, "coin": 140, "tea_ideal": 300, "tea_good": 300, "tea_soft": 300, "tea_splash": 300, "ink_warn": 600, "ink_burst": 600, "ink_lift": 600, "reef_breach": 300, "reef_smash": 90, "reef_crash": 250, "reef_bump": 250}
const CUE_VOLUME_DB := {"click": -12.0, "cook": -15.0, "load": -14.0, "coin": -15.0, "tea_ideal": -11.0, "tea_good": -11.0, "tea_soft": -13.0, "tea_splash": -12.0, "ink_warn": -9.0, "ink_burst": -8.0, "ink_lift": -11.0, "reef_breach": -7.0, "reef_smash": -12.0, "reef_crash": -8.0, "reef_bump": -12.0}
## One looping track per scene; set_scene() crossfades between them.
const MUSIC := {"restaurant": "harbor_cafe", "workshop": "tinker_dock", "dive": "deep_current", "passage": "portal_ride", "boss": "storm_chase"}
const MUSIC_FADE_SECONDS := 0.9
## These start from the top each time; the others pick up where they left off.
const MUSIC_RESTARTS := ["passage", "boss"]
const ALIASES := {"ui": "click", "cooking": "cook", "prepared": "cook", "loading": "load", "loaded": "load", "sale": "coin", "tip": "coin"}

## Each cue that actually starts a voice (tests listen; nothing in play does).
signal cue_played(cue: String)

var music_volume_db := -10.0
var effects_volume_db := 0.0
var _muted := false
var _backgrounded := false
var _focused := true
var music_scene := "restaurant"
var _tracks: Dictionary = {}
var _levels: Dictionary = {}
var _resume: Dictionary = {}
var _sounding: Dictionary = {}
var _voices: Array[AudioStreamPlayer] = []
var _streams: Dictionary = {}
var _last_cue: Dictionary = {}
var _last_any_cue := -1000
var _pour: AudioStreamPlayer

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for key in COOLDOWN_MS:
		_streams[key] = load(AUDIO_PATH + str(key) + ".wav")
	for index in range(VOICE_COUNT):
		var player := AudioStreamPlayer.new()
		player.name = "Cue%s" % index
		add_child(player)
		_voices.append(player)
	# #62: the tea stream, looped while the pour sheet is open; set_pour() follows the flow.
	var stream := load(AUDIO_PATH + "tea_pour.wav") as AudioStreamWAV
	if stream != null:
		var looped := stream.duplicate() as AudioStreamWAV
		looped.loop_mode = AudioStreamWAV.LOOP_FORWARD
		looped.loop_begin = 0
		looped.loop_end = int(round(looped.get_length() * looped.mix_rate))
		_pour = AudioStreamPlayer.new()
		_pour.name = "TeaPour"
		_pour.stream = looped
		add_child(_pour)
	for scene in MUSIC:
		var source := load(AUDIO_PATH + str(MUSIC[scene]) + ".wav") as AudioStreamWAV
		if source == null: continue
		var loop := source.duplicate() as AudioStreamWAV
		loop.loop_mode = AudioStreamWAV.LOOP_FORWARD
		loop.loop_begin = 0
		loop.loop_end = int(round(loop.get_length() * loop.mix_rate))
		var track := AudioStreamPlayer.new()
		track.name = "Music" + str(scene).capitalize()
		track.stream = loop
		add_child(track)
		_tracks[scene] = track
		_levels[scene] = 1.0 if scene == music_scene else 0.0
	_apply_music()
	_sync_pause()

## The music for the scene on screen; crossfades from the current track.
func set_scene(scene: String) -> void:
	if MUSIC.has(scene): music_scene = scene

## How loud a scene's track is right now, 0 to 1 (tests).
func music_level(scene: String) -> float:
	return float(_levels.get(scene, 0.0))

func _process(delta: float) -> void:
	if _muted or _backgrounded or not _focused: return
	for scene in _tracks:
		_levels[scene] = move_toward(float(_levels[scene]), 1.0 if scene == music_scene else 0.0, delta / MUSIC_FADE_SECONDS)
	_apply_music()

func _apply_music() -> void:
	for scene in _tracks:
		var track: AudioStreamPlayer = _tracks[scene]
		var level := float(_levels[scene])
		if level <= 0.0:
			if _sounding.erase(scene):
				if not scene in MUSIC_RESTARTS: _resume[scene] = track.get_playback_position()
				track.stop()
			continue
		track.volume_db = music_volume_db + linear_to_db(level)
		if not _sounding.has(scene):
			_sounding[scene] = true
			track.play(float(_resume.get(scene, 0.0)))

func play_cue(name: String) -> void:
	if _muted or _backgrounded or not _focused or not is_inside_tree():
		return
	var cue: String = ALIASES.get(name, name)
	if not _streams.has(cue):
		return
	var now := Time.get_ticks_msec()
	# Ignore bursts rather than queueing obsolete sounds after a large time step.
	if (cue != "coin" and now - _last_any_cue < 35) or now - int(_last_cue.get(cue, -1000)) < int(COOLDOWN_MS[cue]):
		return
	for voice in _voices:
		if not voice.playing:
			_last_cue[cue] = now
			_last_any_cue = now
			voice.stream = _streams[cue]
			voice.volume_db = float(CUE_VOLUME_DB[cue]) + effects_volume_db
			voice.play()
			cue_played.emit(cue)
			return

## Tea stream loudness for a flow share in [0, 1]; 0 stops it.
func set_pour(flow: float) -> void:
	if _pour == null: return
	var audible := flow > 0.001 and not (_muted or _backgrounded or not _focused) and is_inside_tree()
	if not audible:
		if _pour.playing: _pour.stop()
		return
	_pour.volume_db = linear_to_db(0.25 + 0.75 * clampf(flow, 0.0, 1.0)) - 14.0 + effects_volume_db
	_pour.pitch_scale = 0.9 + 0.25 * clampf(flow, 0.0, 1.0)
	if not _pour.playing: _pour.play()

func set_muted(value: bool) -> void:
	_muted = value
	_sync_pause()

func set_backgrounded(value: bool) -> void:
	_backgrounded = value
	_sync_pause()

func _sync_pause() -> void:
	var quiet := _muted or _backgrounded or not _focused
	if quiet and _pour != null and _pour.playing: _pour.stop()
	for scene in _tracks:
		_tracks[scene].stream_paused = quiet
	# Never resume stale coin/cooking/UI sounds after returning to the app.
	if quiet:
		for voice in _voices:
			voice.stop()

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_PAUSED:
		set_backgrounded(true)
	elif what == NOTIFICATION_APPLICATION_RESUMED:
		set_backgrounded(false)
	elif what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		_focused = false
		_sync_pause()
	elif what == NOTIFICATION_APPLICATION_FOCUS_IN:
		_focused = true
		_sync_pause()

## Silences every track at once (teardown).
func stop_music() -> void:
	_sounding.clear()
	for scene in _tracks:
		_tracks[scene].stop()

func _exit_tree() -> void:
	stop_music()
	for voice in _voices:
		voice.stop()
