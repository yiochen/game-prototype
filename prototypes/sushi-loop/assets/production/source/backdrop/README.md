# Approved restaurant backdrop sources

`restaurant-backdrop-35.blend` is the approved editable gate and plain wall study,
with ordinary 35° orthographic cameras and uniform lighting. The original full
PNG exports are copied byte-for-byte into the production and Godot catalogs.
The model was approved after the wall color, baseboard and lighting revision.

The original builder, renderer and lighting proof remain under
`assets/restaurant-backdrop/uniform35/`. Camera, geometry and source hash receipts
are copied alongside this file. Native wall-plane registration is separate from
the older environment square-top/front projection.

`tools/publish_restaurant_backdrop.py` publishes the two catalog objects, retires
the old entrance exports and updates variant catalog bindings only while all
character and feedback base records remain identical. Original variant capture
provenance remains intact. `tools/retire_entrance_model.py` removes the old model
from the current editable master and adds the approved backdrop scene. Immutable
source snapshots remain the provenance authority for unrelated approved assets.
