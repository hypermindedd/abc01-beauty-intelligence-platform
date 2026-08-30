from __future__ import annotations
from typing import Any

CATALOG_VERSION = "2026.08.1"

HAIR_LENGTH_ORDER = {"BALD":0,"VERY_SHORT":1,"SHORT":2,"MEDIUM":3,"LONG":4,"VERY_LONG":5,"UNKNOWN":2}
MAINTENANCE_ORDER = {"Low":0,"Low–Moderate":1,"Moderate":2,"High":3}
CHANGE_ORDER = {"Subtle":0,"Noticeable":1,"Statement":2}
BEARD_COVERAGE_ORDER = {"NONE":0,"STUBBLE":1,"SPARSE":1,"PARTIAL":2,"MEDIUM":3,"FULL":4,"UNKNOWN":0}

# Trend-current entries are grounded in 2026 editorial/barber coverage; evergreen entries remain
# available because ABC is a salon decision system, not a trend-only feed.
HAIR_STYLES: list[dict[str,Any]] = [
    {"id":"H001","name":"Soft / White-Collar Mullet","family":"mullet","min_length":"MEDIUM","maintenance":"Moderate","change":"Statement","textures":["STRAIGHT","WAVY","CURLY"],"tags":["current","2026","modern","soft","editorial","texture"],"occasions":["Everyday","Party","Photoshoot"],"trend":"CURRENT_2026","trend_note":"Softer, wearable mullet with controlled back length."},
    {"id":"H002","name":"Burst Fade","family":"fade","min_length":"SHORT","maintenance":"Moderate","change":"Noticeable","textures":["WAVY","CURLY","COILY","STRAIGHT"],"tags":["current","2026","modern","contrast","texture"],"occasions":["Everyday","Party","Photoshoot"],"trend":"CURRENT_2026","trend_note":"Circular fade around the ear while preserving top/back character."},
    {"id":"H003","name":"Tailored Buzz Cut","family":"buzz","min_length":"VERY_SHORT","maintenance":"Low","change":"Noticeable","textures":["ANY"],"tags":["current","2026","tailored","clean","low-maintenance","professional"],"occasions":["Everyday","Business","Groom"],"trend":"CURRENT_2026","trend_note":"Customized buzz with considered fade/neckline rather than a generic clipper cut."},
    {"id":"H004","name":"Crew Cut","family":"crew","min_length":"SHORT","maintenance":"Low","change":"Subtle","textures":["ANY"],"tags":["current","2026","classic","professional","clean","wearable"],"occasions":["Everyday","Business","Groom"],"trend":"CURRENT_2026","trend_note":"Timeless short cut with softer tapering and tailored finish."},
    {"id":"H005","name":"Textured Caesar","family":"crop","min_length":"SHORT","maintenance":"Low","change":"Noticeable","textures":["STRAIGHT","WAVY","CURLY"],"tags":["current","2026","texture","fringe","wearable","modern"],"occasions":["Everyday","Business"],"trend":"CURRENT_2026","trend_note":"Short textured fringe with a controlled, wearable silhouette."},
    {"id":"H006","name":"Modern Curtains","family":"part","min_length":"MEDIUM","maintenance":"Moderate","change":"Noticeable","textures":["STRAIGHT","WAVY","CURLY"],"tags":["current","2026","center-part","soft","flow","modern"],"occasions":["Everyday","Business","Party"],"trend":"CURRENT_2026","trend_note":"Updated curtains with natural movement rather than rigid 90s styling."},
    {"id":"H007","name":"Messy Center Part","family":"part","min_length":"MEDIUM","maintenance":"Moderate","change":"Noticeable","textures":["STRAIGHT","WAVY"],"tags":["current","2026","center-part","texture","natural","soft"],"occasions":["Everyday","Party","Photoshoot"],"trend":"CURRENT_2026","trend_note":"Layered center part designed for touchable movement."},
    {"id":"H008","name":"Tailored Side Part","family":"part","min_length":"SHORT","maintenance":"Moderate","change":"Subtle","textures":["STRAIGHT","WAVY"],"tags":["current","2026","refined","formal","professional","camera","classic"],"occasions":["Business","Groom","Photoshoot"],"trend":"CURRENT_2026","trend_note":"Formal side part returning in a cleaner, less rigid form."},
    {"id":"H009","name":"Soft Taper / Natural Neckline","family":"taper","min_length":"SHORT","maintenance":"Low–Moderate","change":"Subtle","textures":["ANY"],"tags":["current","2026","soft","tailored","professional","natural","wearable"],"occasions":["Everyday","Business","Groom"],"trend":"CURRENT_2026","trend_note":"2026 emphasis on quieter tapers and natural grow-out."},
    {"id":"H010","name":"Low Taper + Textured Top","family":"taper","min_length":"SHORT","maintenance":"Low–Moderate","change":"Noticeable","textures":["STRAIGHT","WAVY","CURLY"],"tags":["modern","professional","texture","wearable","camera"],"occasions":["Everyday","Business","Groom","Photoshoot"],"trend":"CORE_CURRENT","trend_note":"Modern salon staple with controlled contrast."},
    {"id":"H011","name":"Low Fade + Natural Top","family":"fade","min_length":"SHORT","maintenance":"Moderate","change":"Noticeable","textures":["ANY"],"tags":["fade","clean","modern","professional"],"occasions":["Everyday","Business","Groom"],"trend":"CORE_CURRENT","trend_note":"Low fade keeps more fullness and reads more classic than high contrast fades."},
    {"id":"H012","name":"Mid Fade + Textured Top","family":"fade","min_length":"SHORT","maintenance":"Moderate","change":"Noticeable","textures":["ANY"],"tags":["fade","modern","texture","versatile"],"occasions":["Everyday","Business","Party"],"trend":"CORE_CURRENT","trend_note":"Versatile mid-height graduation."},
    {"id":"H013","name":"High Fade + Structured Top","family":"fade","min_length":"SHORT","maintenance":"High","change":"Statement","textures":["ANY"],"tags":["fade","contrast","bold","sharp"],"occasions":["Everyday","Party"],"trend":"AVAILABLE_NOT_DOMINANT_2026","trend_note":"Still valid, but 2026 is shifting toward softer/natural cuts."},
    {"id":"H014","name":"Textured Crop / No-Fade Crop","family":"crop","min_length":"SHORT","maintenance":"Low","change":"Noticeable","textures":["STRAIGHT","WAVY","CURLY"],"tags":["current","2026","texture","natural","low-maintenance","fringe"],"occasions":["Everyday","Business"],"trend":"CURRENT_2026","trend_note":"Texture and length are increasingly replacing default skin fades."},
    {"id":"H015","name":"Textured Fringe","family":"fringe","min_length":"MEDIUM","maintenance":"Moderate","change":"Noticeable","textures":["STRAIGHT","WAVY","CURLY"],"tags":["current","2026","fringe","boy-bangs","texture","modern"],"occasions":["Everyday","Party","Photoshoot"],"trend":"CURRENT_2026","trend_note":"Fringes / boy bangs are a visible 2026 direction."},
    {"id":"H016","name":"Curly Fringe","family":"fringe","min_length":"MEDIUM","maintenance":"Moderate","change":"Noticeable","textures":["CURLY","COILY","WAVY"],"tags":["current","texture","natural","fringe"],"occasions":["Everyday","Party"],"trend":"CORE_CURRENT","trend_note":"Keeps natural texture as the focal point."},
    {"id":"H017","name":"Classic Slick Back","family":"slick","min_length":"MEDIUM","maintenance":"High","change":"Noticeable","textures":["STRAIGHT","WAVY"],"tags":["formal","refined","camera","classic","polished"],"occasions":["Business","Groom","Photoshoot"],"trend":"CORE_CURRENT","trend_note":"Formal classic still relevant when adapted to natural density."},
    {"id":"H018","name":"Soft Slick Back / Pushed Back Flow","family":"slick","min_length":"MEDIUM","maintenance":"Moderate","change":"Noticeable","textures":["STRAIGHT","WAVY","CURLY"],"tags":["current","2026","soft","flow","refined","camera"],"occasions":["Business","Groom","Party","Photoshoot"],"trend":"CURRENT_2026","trend_note":"Longer pushed-back styling with less rigid hold."},
    {"id":"H019","name":"Modern Quiff","family":"quiff","min_length":"MEDIUM","maintenance":"High","change":"Statement","textures":["STRAIGHT","WAVY"],"tags":["volume","formal","bold","camera","polished"],"occasions":["Groom","Party","Photoshoot"],"trend":"CORE_CURRENT","trend_note":"High-volume formal option when source length supports it."},
    {"id":"H020","name":"French Crop","family":"crop","min_length":"SHORT","maintenance":"Low","change":"Noticeable","textures":["ANY"],"tags":["classic","fringe","low-maintenance","clean"],"occasions":["Everyday","Business"],"trend":"EVERGREEN","trend_note":"Practical short crop with controlled fringe."},
    {"id":"H021","name":"Ivy League","family":"crew","min_length":"SHORT","maintenance":"Low–Moderate","change":"Subtle","textures":["STRAIGHT","WAVY"],"tags":["classic","professional","refined","wearable"],"occasions":["Business","Groom","Everyday"],"trend":"EVERGREEN","trend_note":"Polished short style with side-part flexibility."},
    {"id":"H022","name":"Scissor Taper","family":"taper","min_length":"SHORT","maintenance":"Low–Moderate","change":"Subtle","textures":["ANY"],"tags":["natural","professional","soft","tailored"],"occasions":["Business","Groom","Everyday"],"trend":"CORE_CURRENT","trend_note":"Natural scissor-led taper with softer grow-out."},
    {"id":"H023","name":"Bro Flow","family":"flow","min_length":"LONG","maintenance":"Moderate","change":"Subtle","textures":["STRAIGHT","WAVY","CURLY"],"tags":["flow","natural","soft","long"],"occasions":["Everyday","Party","Photoshoot"],"trend":"CORE_CURRENT","trend_note":"Longer, relaxed movement with minimal hard structure."},
    {"id":"H024","name":"Beachy Waves","family":"flow","min_length":"LONG","maintenance":"Moderate","change":"Subtle","textures":["WAVY","CURLY","STRAIGHT"],"tags":["current","2026","natural","flow","texture","long"],"occasions":["Everyday","Party","Photoshoot"],"trend":"CURRENT_2026","trend_note":"Natural long-hair direction with loose movement."},
    {"id":"H025","name":"Layered Shag","family":"shag","min_length":"LONG","maintenance":"Moderate","change":"Statement","textures":["STRAIGHT","WAVY","CURLY"],"tags":["current","2026","shag","texture","editorial","long"],"occasions":["Everyday","Party","Photoshoot"],"trend":"CURRENT_2026","trend_note":"Layered, controlled wildness rather than rigid styling."},
    {"id":"H026","name":"Wolf Cut","family":"mullet","min_length":"MEDIUM","maintenance":"Moderate","change":"Statement","textures":["STRAIGHT","WAVY","CURLY"],"tags":["mullet","shag","editorial","texture"],"occasions":["Everyday","Party","Photoshoot"],"trend":"CORE_CURRENT","trend_note":"Shag/mullet hybrid; only feasible with enough source length."},
    {"id":"H027","name":"Soft Punk Layers","family":"shag","min_length":"LONG","maintenance":"High","change":"Statement","textures":["STRAIGHT","WAVY"],"tags":["current","2026","editorial","punk","layers","bold"],"occasions":["Party","Photoshoot"],"trend":"CURRENT_2026","trend_note":"Structured long layers with rebellious edge."},
    {"id":"H028","name":"Full-Grown Curls","family":"natural-curl","min_length":"LONG","maintenance":"Moderate","change":"Subtle","textures":["CURLY","COILY"],"tags":["current","2026","natural","texture","long"],"occasions":["Everyday","Party","Photoshoot"],"trend":"CURRENT_2026","trend_note":"Emphasizes natural curl pattern rather than forcing a fade."},
    {"id":"H029","name":"Grown-Out Afro","family":"natural-curl","min_length":"LONG","maintenance":"Moderate","change":"Subtle","textures":["COILY","CURLY"],"tags":["current","2026","natural","texture","long"],"occasions":["Everyday","Party","Photoshoot"],"trend":"CURRENT_2026","trend_note":"Natural textured volume with shape maintenance."},
    {"id":"H030","name":"Modern Bowl / Layered Bowl","family":"bowl","min_length":"MEDIUM","maintenance":"High","change":"Statement","textures":["STRAIGHT","WAVY","CURLY"],"tags":["current","2026","editorial","fashion","fringe","bold"],"occasions":["Party","Photoshoot"],"trend":"CURRENT_2026","trend_note":"High-fashion layered bowl with texture and tapered perimeter."},
    {"id":"H031","name":"Faux Hawk","family":"mohawk","min_length":"MEDIUM","maintenance":"High","change":"Statement","textures":["ANY"],"tags":["bold","texture","contrast"],"occasions":["Party","Photoshoot"],"trend":"AVAILABLE","trend_note":"Statement option; not a default recommendation."},
    {"id":"H032","name":"Pompadour","family":"quiff","min_length":"MEDIUM","maintenance":"High","change":"Statement","textures":["STRAIGHT","WAVY"],"tags":["classic","volume","formal","bold"],"occasions":["Groom","Party","Photoshoot"],"trend":"EVERGREEN","trend_note":"High-commitment volume style requiring source length and styling tolerance."},
    {"id":"H033","name":"Side Sweep","family":"part","min_length":"MEDIUM","maintenance":"Moderate","change":"Subtle","textures":["STRAIGHT","WAVY"],"tags":["refined","formal","professional","soft"],"occasions":["Business","Groom","Photoshoot"],"trend":"EVERGREEN","trend_note":"Soft formal direction with lower visual risk."},
    {"id":"H034","name":"Curly Taper","family":"taper","min_length":"SHORT","maintenance":"Low–Moderate","change":"Noticeable","textures":["CURLY","COILY"],"tags":["natural","texture","modern","clean"],"occasions":["Everyday","Business","Groom"],"trend":"CORE_CURRENT","trend_note":"Preserves curl character while cleaning perimeter."},
    {"id":"H035","name":"Buzz + Tapered Neckline","family":"buzz","min_length":"VERY_SHORT","maintenance":"Low","change":"Noticeable","textures":["ANY"],"tags":["current","2026","buzz","tailored","clean"],"occasions":["Everyday","Business","Groom"],"trend":"CURRENT_2026","trend_note":"A refined buzz variation with considered edges."},
    {"id":"H036","name":"Long Slickback","family":"slick","min_length":"LONG","maintenance":"High","change":"Noticeable","textures":["STRAIGHT","WAVY","CURLY"],"tags":["current","2026","formal","long","polished"],"occasions":["Groom","Business","Photoshoot"],"trend":"CURRENT_2026","trend_note":"Long hair cleaned back for formal/event use."},
]

BEARD_STYLES: list[dict[str,Any]] = [
    {"id":"B001","name":"Clean Shave / Clean Contour","min_coverage":"NONE","maintenance":"Low","change":"Subtle","tags":["clean","professional","natural"],"trend":"EVERGREEN"},
    {"id":"B002","name":"Light Stubble","min_coverage":"STUBBLE","maintenance":"Low","change":"Subtle","tags":["current","2026","stubble","natural","professional"],"trend":"CURRENT_2026"},
    {"id":"B003","name":"Executive Stubble","min_coverage":"STUBBLE","maintenance":"Low–Moderate","change":"Subtle","tags":["current","2026","stubble","refined","professional"],"trend":"CURRENT_2026"},
    {"id":"B004","name":"Heavy Stubble","min_coverage":"STUBBLE","maintenance":"Low–Moderate","change":"Noticeable","tags":["stubble","rugged","natural"],"trend":"CORE_CURRENT"},
    {"id":"B005","name":"Natural Sparse Stubble Cleanup","min_coverage":"SPARSE","maintenance":"Low","change":"Subtle","tags":["reality-safe","natural","cleanup"],"trend":"ABC_REALITY_SAFE"},
    {"id":"B006","name":"Anchored Stache","min_coverage":"PARTIAL","maintenance":"Moderate","change":"Noticeable","tags":["current","2026","moustache","chin"],"trend":"CURRENT_2026"},
    {"id":"B007","name":"Minimal Goatee","min_coverage":"PARTIAL","maintenance":"Moderate","change":"Noticeable","tags":["goatee","clean"],"trend":"CORE_CURRENT"},
    {"id":"B008","name":"Van Dyke","min_coverage":"PARTIAL","maintenance":"High","change":"Statement","tags":["current","2026","moustache","goatee","statement"],"trend":"CURRENT_2026"},
    {"id":"B009","name":"Circle Beard","min_coverage":"PARTIAL","maintenance":"Moderate","change":"Noticeable","tags":["circle","professional"],"trend":"CORE_CURRENT"},
    {"id":"B010","name":"Short Boxed Beard","min_coverage":"MEDIUM","maintenance":"Moderate","change":"Noticeable","tags":["boxed","refined","professional"],"trend":"CORE_CURRENT"},
    {"id":"B011","name":"Corporate Beard","min_coverage":"MEDIUM","maintenance":"Moderate","change":"Noticeable","tags":["corporate","professional","refined"],"trend":"CORE_CURRENT"},
    {"id":"B012","name":"Tapered Beard","min_coverage":"MEDIUM","maintenance":"Moderate","change":"Noticeable","tags":["current","2026","tapered","natural-growout"],"trend":"CURRENT_2026"},
    {"id":"B013","name":"Low-Fade Beard","min_coverage":"MEDIUM","maintenance":"Moderate","change":"Noticeable","tags":["current","2026","fade","refined"],"trend":"CURRENT_2026"},
    {"id":"B014","name":"Beardstache","min_coverage":"MEDIUM","maintenance":"Moderate","change":"Statement","tags":["current","2026","moustache","stubble"],"trend":"CURRENT_2026"},
    {"id":"B015","name":"Classic Full Beard","min_coverage":"FULL","maintenance":"High","change":"Noticeable","tags":["current","2026","full","classic"],"trend":"CURRENT_2026"},
    {"id":"B016","name":"Sculpted Full Beard","min_coverage":"FULL","maintenance":"High","change":"Statement","tags":["full","sculpted","formal"],"trend":"CORE_CURRENT"},
]

STYLE_CONTEXT_TAGS = {
    "Refined":["refined","professional","tailored","formal","polished","clean"],
    "Natural":["natural","soft","wearable","low-maintenance","flow"],
    "Modern":["modern","current","2026","texture","tailored"],
    "Bold":["bold","contrast","statement","editorial"],
    "Editorial":["editorial","fashion","trend-forward","current","2026"],
    "Luxury":["refined","polished","formal","camera","tailored"],
}

OCCASION_TAGS = {
    "Groom":["formal","camera","refined","polished","groom"],
    "Business":["professional","refined","clean","wearable"],
    "Birthday":["modern","wearable","current","texture"],
    "Party":["modern","bold","editorial","texture"],
    "Everyday":["wearable","natural","low-maintenance","soft"],
    "Photoshoot":["camera","editorial","polished","texture","formal"],
}

TREND_SOURCES = [
    {"publisher":"GQ","published":"2026-01-16","title":"The Best Men's Hair Trends of 2026","coverage":["Center Parts","Side Parts","Manageable Mullets","Tailored Buzzcuts"]},
    {"publisher":"GQ","published":"2026-01-20","title":"The 7 Best Short Haircuts For Men in 2026","coverage":["Soft Mullet","Burst Fade","Buzz Cut","Crew Cut","Caesar","Curtains","Bowl Cut"]},
    {"publisher":"GQ","published":"2026-07-31","title":"Everything You Need to Know About Fade Haircuts","coverage":["Low Fade","Mid Fade","High Fade","Taper Fade"]},
    {"publisher":"GQ","published":"2026-02-26","title":"The Best Beard Styles of 2026, According to Barbers","coverage":["Tapered Beard","Low Fade Beard","Beardstache","Stubble Beard","Anchored Stache","Van Dyke","Classic Full Beard"]},
]

def catalog_payload() -> dict[str,Any]:
    return {
        "version":CATALOG_VERSION,
        "hair_styles":HAIR_STYLES,
        "beard_styles":BEARD_STYLES,
        "trend_sources":TREND_SOURCES,
        "note":"Open-ended salon registry: current 2026 directions + evergreen/core styles. Extend without changing canonical recommendation roles.",
    }

COLOR_DIRECTIONS: list[dict[str,Any]] = [
    {"id":"C001","name":"Natural Gray Blend","maintenance":"Moderate","change":"Subtle","tags":["natural","gray","professional","low-contrast"],"trend":"CORE_CURRENT","trend_note":"Reduces gray contrast while preserving dimension."},
    {"id":"C002","name":"Soft Salt & Pepper","maintenance":"Low–Moderate","change":"Subtle","tags":["natural","gray","low-maintenance"],"trend":"CORE_CURRENT","trend_note":"Preserves natural variation and softer regrowth."},
    {"id":"C003","name":"Cool Espresso","maintenance":"Moderate","change":"Noticeable","tags":["refined","dark","cool","professional"],"trend":"CORE_CURRENT","trend_note":"Deeper cool-toned direction for a polished result."},
    {"id":"C004","name":"Neutral Dark Brown","maintenance":"Moderate","change":"Noticeable","tags":["natural","dark","neutral","professional"],"trend":"EVERGREEN","trend_note":"Balanced dark direction without an overly warm or cool cast."},
    {"id":"C005","name":"Warm Chestnut","maintenance":"Moderate","change":"Noticeable","tags":["warm","brown","soft"],"trend":"CORE_CURRENT","trend_note":"Adds controlled warmth and visible dimension."},
    {"id":"C006","name":"Ash Brown","maintenance":"Moderate","change":"Noticeable","tags":["ash","cool","modern"],"trend":"CORE_CURRENT","trend_note":"Muted cool direction for a cleaner modern read."},
    {"id":"C007","name":"Smoky Charcoal","maintenance":"High","change":"Statement","tags":["smoky","editorial","cool","bold"],"trend":"CURRENT_2026","trend_note":"Editorial gray/charcoal direction; feasibility remains specialist-controlled."},
    {"id":"C008","name":"Silver Blend","maintenance":"High","change":"Statement","tags":["silver","gray","editorial"],"trend":"CORE_CURRENT","trend_note":"Higher-contrast silver direction requiring professional feasibility review."},
    {"id":"C009","name":"Polished Espresso Event","maintenance":"Moderate","change":"Noticeable","tags":["formal","camera","refined","dark"],"trend":"CORE_CURRENT","trend_note":"Event-oriented deeper tone direction."},
    {"id":"C010","name":"Soft Black / Natural Black","maintenance":"Moderate","change":"Noticeable","tags":["dark","formal","classic"],"trend":"EVERGREEN","trend_note":"Deep dark direction without blue-black exaggeration."},
    {"id":"C011","name":"Honey / Golden Accent Direction","maintenance":"High","change":"Statement","tags":["warm","accent","bold"],"trend":"CURRENT_2026","trend_note":"Warm accent direction; any lightening requires professional check."},
    {"id":"C012","name":"Platinum / Bleach Direction","maintenance":"High","change":"Statement","tags":["bleach","editorial","bold","current","2026"],"trend":"CURRENT_2026","trend_note":"Trend-forward but high-control; Preview is not chemical feasibility proof."},
]

# redefine payload after COLOR_DIRECTIONS declaration
def catalog_payload() -> dict[str,Any]:
    return {
        "version":CATALOG_VERSION,
        "hair_styles":HAIR_STYLES,
        "beard_styles":BEARD_STYLES,
        "color_directions":COLOR_DIRECTIONS,
        "trend_sources":TREND_SOURCES,
        "note":"Open-ended salon registry: current 2026 directions + evergreen/core styles. Extend without changing canonical recommendation roles.",
    }
