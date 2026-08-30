from __future__ import annotations
from typing import Any

# Component-oriented catalog. Named styles are optional references, not the sole
# recommendation unit. A recommendation can be a custom composition of components.

HAIR_COMPONENTS = [
    {"id":"HC01","name":"Soft perimeter refinement","kind":"perimeter","change":"Subtle","maintenance":"Low","tags":["natural","refined","professional"]},
    {"id":"HC02","name":"Controlled face-framing layers","kind":"shape","change":"Noticeable","maintenance":"Moderate","tags":["soft","modern","movement"]},
    {"id":"HC03","name":"Textured top / crown redistribution","kind":"texture","change":"Noticeable","maintenance":"Moderate","tags":["modern","texture","volume"]},
    {"id":"HC04","name":"Reduced side width / cleaner silhouette","kind":"silhouette","change":"Noticeable","maintenance":"Low–Moderate","tags":["refined","clean","formal"]},
    {"id":"HC05","name":"Soft fringe / front movement","kind":"front","change":"Noticeable","maintenance":"Moderate","tags":["soft","modern","youthful-neutral"]},
    {"id":"HC06","name":"Polished event finish","kind":"finish","change":"Subtle","maintenance":"Moderate","tags":["formal","camera","event"]},
    {"id":"HC07","name":"Natural texture preservation","kind":"texture","change":"Subtle","maintenance":"Low","tags":["natural","low-maintenance"]},
    {"id":"HC08","name":"Statement structure / editorial finish","kind":"finish","change":"Statement","maintenance":"High","tags":["editorial","bold","camera"]},
]

COLOR_COMPONENTS = [
    {"id":"CC01","name":"Neutral depth refinement","change":"Subtle","maintenance":"Low–Moderate","tags":["neutral","professional","natural"]},
    {"id":"CC02","name":"Soft dimensional contrast","change":"Noticeable","maintenance":"Moderate","tags":["dimension","soft","modern"]},
    {"id":"CC03","name":"Warm dimensional direction","change":"Noticeable","maintenance":"Moderate","tags":["warm","soft"]},
    {"id":"CC04","name":"Cool muted direction","change":"Noticeable","maintenance":"Moderate","tags":["cool","modern","refined"]},
    {"id":"CC05","name":"Gray-blend / lower-contrast direction","change":"Subtle","maintenance":"Low–Moderate","tags":["gray","natural","low-maintenance"]},
    {"id":"CC06","name":"High-contrast editorial direction","change":"Statement","maintenance":"High","tags":["editorial","bold","high-control"]},
]

MAKEUP_COMPONENTS = [
    {"id":"MC01","name":"Natural complexion balance","domain":"complexion","change":"Subtle","maintenance":"Low","tags":["natural","day","camera"]},
    {"id":"MC02","name":"Soft eye definition","domain":"eyes","change":"Subtle","maintenance":"Low","tags":["soft","refined"]},
    {"id":"MC03","name":"Defined eye / event emphasis","domain":"eyes","change":"Noticeable","maintenance":"Moderate","tags":["event","formal","camera"]},
    {"id":"MC04","name":"Balanced brow framing","domain":"brows","change":"Subtle","maintenance":"Low","tags":["refined","natural"]},
    {"id":"MC05","name":"Soft lip color focus","domain":"lips","change":"Noticeable","maintenance":"Moderate","tags":["soft","event"]},
    {"id":"MC06","name":"Glam / editorial contrast","domain":"full","change":"Statement","maintenance":"High","tags":["glam","editorial","formal"]},
]

NAIL_COMPONENTS = [
    {"id":"NC01","name":"Natural short shape refinement","domain":"shape","change":"Subtle","maintenance":"Low","tags":["natural","clean","professional"]},
    {"id":"NC02","name":"Soft almond direction","domain":"shape","change":"Noticeable","maintenance":"Moderate","tags":["refined","soft"]},
    {"id":"NC03","name":"Classic French direction","domain":"surface","change":"Noticeable","maintenance":"Moderate","tags":["classic","bridal","formal"]},
    {"id":"NC04","name":"Minimal graphic accent","domain":"surface","change":"Noticeable","maintenance":"Moderate","tags":["minimal","modern"]},
    {"id":"NC05","name":"Luxury editorial design","domain":"surface","change":"Statement","maintenance":"High","tags":["luxury","editorial","event"]},
    {"id":"NC06","name":"Fantasy nail-art composition","domain":"surface","change":"Statement","maintenance":"High","tags":["art","bold","editorial"]},
]

BEARD_COMPONENTS = [
    {"id":"BC01","name":"Existing stubble cleanup","min_coverage":"STUBBLE","change":"Subtle","maintenance":"Low","tags":["natural","cleanup"]},
    {"id":"BC02","name":"Natural contour refinement","min_coverage":"SPARSE","change":"Subtle","maintenance":"Low","tags":["natural","refined"]},
    {"id":"BC03","name":"Short shape definition","min_coverage":"PARTIAL","change":"Noticeable","maintenance":"Moderate","tags":["defined","formal"]},
    {"id":"BC04","name":"Moustache/chin coordination","min_coverage":"PARTIAL","change":"Noticeable","maintenance":"Moderate","tags":["moustache","chin"]},
    {"id":"BC05","name":"Short boxed direction","min_coverage":"MEDIUM","change":"Noticeable","maintenance":"Moderate","tags":["boxed","professional"]},
    {"id":"BC06","name":"Full sculpted direction","min_coverage":"FULL","change":"Statement","maintenance":"High","tags":["full","sculpted","formal"]},
]

ROLE_INTENT = {
    "BEST FIT":"strongest balanced fit under current evidence and preferences",
    "ALTERNATIVE":"valid lower-burden or meaningfully different trade-off",
    "BOLDER":"valid higher-change direction without crossing evidence/safety boundaries",
    "EXPLORE":"additional valid direction; never filler and never allowed to relabel Core roles",
}


def catalog_payload() -> dict[str, Any]:
    return {
        "version":"0.4.0",
        "hair_components":HAIR_COMPONENTS,
        "color_components":COLOR_COMPONENTS,
        "makeup_components":MAKEUP_COMPONENTS,
        "nail_components":NAIL_COMPONENTS,
        "beard_components":BEARD_COMPONENTS,
        "role_intent":ROLE_INTENT,
        "rule":"Named styles may be used as references, but recommendations may be custom component compositions.",
    }
