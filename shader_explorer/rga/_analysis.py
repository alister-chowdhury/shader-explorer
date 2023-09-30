import csv
import re

_EXTRACT_REGISTER_RE = re.compile(
    # vX
    # v[X:Y]
    # sX
    # s[X:Y]
    r"\b(s|v)(\d+|\[\d+\:\d+\])"
)

_EXTRACT_LABEL_OFFSETS = re.compile(
    # _label:
    r"^\s*([^:\s]+):"
    # v_inst xxxx // 000000000000
    r"\s*.+?//\s*(?:0x)?([0-9A-Fa-f]+)",
    flags = re.MULTILINE
)


def _predict_register_occupancy(used, available, min_offset):
    return 1 - max(
        0, min(1, (used - min_offset) / max(1, (available - min_offset)))
    )


def _extract_label_offsets(isa_path):
    with open(isa_path, "r") as in_fp:
        amdisa = in_fp.read()
    return {
        label: int(offset, 16)
        for label, offset in _EXTRACT_LABEL_OFFSETS.findall(
            amdisa
        )
    }

def rga_analyse(rga_compiled_shader):
    
    with open(anaylsis_csv, "r") as in_fp:
        reader = csv.DictReader(in_fp)
        top_level_analysis = next(reader)
    
    top_level_analysis = {
        k.lower(): int(v) if v.isnumeric() else v
        for k, v in top_level_analysis.items()
    }


    # Hand wavey analysis
    min_sgpr = 6
    min_vgpr = 4
    min_lds = 16384  # todo

    if all(k in top_level_analysis for k in ("used_sgprs", "available_sgprs")):
        predicted_occupancy_sgpr = _predict_register_occupancy(
            top_level_analysis["used_sgprs"],
            top_level_analysis["available_sgprs"],
            min_sgpr,
        )
    else:
        predicted_occupancy_sgpr = 1
    
    if all(k in top_level_analysis for k in ("used_vgprs", "available_vgprs")):
        predicted_occupancy_vgpr = _predict_register_occupancy(
            top_level_analysis["used_vgprs"],
            top_level_analysis["available_vgprs"],
            min_vgpr,
        )
    else:
        predicted_occupancy_vgpr = 1
    
    if all(
        k in top_level_analysis
        for k in ("used_lds_bytes", "available_lds_bytes")
    ):
        predicted_occupancy_lds = _predict_register_occupancy(
            top_level_analysis["used_lds_bytes"],
            top_level_analysis["available_lds_bytes"],
            min_lds,
        )
    else:
        predicted_occupancy_lds = 1
    
    predicted_occupancy = min(
        predicted_occupancy_sgpr,
        min(predicted_occupancy_vgpr, predicted_occupancy_lds),
    )
