"""What we ask families to capture. The likeness page and the API both read from here."""

# (key, label, hint)
SLOT_GROUPS = [
    ("Views", "photo", [
        ("front", "Straight on, from the front", "At their eye level, standing square."),
        ("side_left", "Left side", "The whole dog in frame, standing."),
        ("side_right", "Right side", "The whole dog in frame, standing."),
        ("three_quarter_left", "Three-quarter, front left", "Halfway between the front and the side."),
        ("three_quarter_right", "Three-quarter, front right", "Halfway between the front and the side."),
        ("rear", "From behind", "Standing, tail relaxed."),
        ("above", "From above", "Standing, looking straight down on their back."),
    ]),
    ("Face", "photo", [
        ("eyes", "Eyes", "Close, in soft light, so we can see their colour and depth."),
        ("nose", "Nose", "Straight on and from the side."),
        ("whiskers", "Whisker pads", "Both sides of the muzzle."),
        ("ears", "Ear set", "How the ears sit at rest, and when alert."),
    ]),
    ("Character", "photo", [
        ("markings", "Markings, scars and coat pattern", "Anything that makes them unmistakably them."),
        ("standing", "Standing, in their normal posture", "How they stand when nobody is asking them to."),
        ("sitting", "Sitting", "Their usual sit."),
    ]),
    ("Film", "video", [
        ("walking", "Walking and looking around", "10 to 20 seconds, so we can see their expression and how the coat moves. 1080p is plenty."),
    ]),
]

SLOTS = {key: {"label": label, "hint": hint, "kind": kind, "group": group}
         for group, kind, items in SLOT_GROUPS for key, label, hint in items}

# (key, label, hint). Stored as entered, with the unit of the round.
MEASUREMENTS = [
    ("nose_to_tail", "Nose to base of tail", "Along the back, following the spine."),
    ("withers_height", "Height at withers", "Floor to the top of the shoulders, standing square."),
    ("chest_girth", "Chest girth", "Around the widest part of the chest."),
    ("neck", "Neck circumference", "Where the collar sits."),
    ("head_length", "Head length", "Tip of the nose to the back of the skull."),
    ("head_width", "Head width", "Across the widest point, between the ears."),
    ("front_paw_width", "Front paw width", "Standing, across the widest point."),
    ("front_paw_length", "Front paw length", "Standing, heel pad to the tip of the longest toe."),
    ("rear_paw_width", "Rear paw width", "Standing, across the widest point."),
    ("rear_paw_length", "Rear paw length", "Standing, heel pad to the tip of the longest toe."),
]
MEASUREMENT_KEYS = [k for k, _, _ in MEASUREMENTS]

UNITS = {"in": 2.54, "cm": 1.0}  # factor to centimetres

IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/heic": ".heic", "image/heif": ".heif"}
VIDEO_TYPES = {"video/mp4": ".mp4", "video/quicktime": ".mov", "video/webm": ".webm"}
