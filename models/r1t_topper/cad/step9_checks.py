"""Deterministic checks for Step 9 mounts, controls, crossbars, and keep-outs."""

from math import isclose

from mount_interfaces import (
    build_mount_interface_subassembly,
    make_quick_release_mount_adapters,
    make_relocated_control_system,
    make_topper_crossbar_ports,
    make_vehicle_and_service_keepouts,
)
from parameters import (
    DESIGN_DECISION,
    PLACEHOLDER_REQUIRING_SCAN,
    bed_anchor_locations,
    bed_control_functions,
    crossbar_interface_depth,
    crossbar_interface_width,
    crossbar_mount_span,
    mount_adapter_pad_size,
    mount_receiver_size,
    relocated_control_pod_height,
    topper_crossbar_station_1,
    topper_crossbar_station_2,
    topper_overall_length,
    value,
)
from topper_envelope import make_base_flange_references, make_engineered_shell
from vehicle_reference import make_anchor_references, make_keep_out_zones


def _close(actual: float, expected: float) -> None:
    assert isclose(actual, expected, abs_tol=1e-6), (actual, expected)


def _by_label(items):
    return {item.label: item for item in items}


def run() -> None:
    adapters = make_quick_release_mount_adapters().children
    assert len(adapters) == 12
    assert mount_adapter_pad_size.provenance == DESIGN_DECISION
    assert mount_receiver_size.provenance == PLACEHOLDER_REQUIRING_SCAN
    anchors = make_anchor_references().children
    flanges = make_base_flange_references().children
    for index, ((x, y, _z), anchor) in enumerate(
        zip(value(bed_anchor_locations), anchors), start=1
    ):
        station = _by_label(item for item in adapters if f"MOUNT_{index}_" in item.label)
        pad = station[f"MOUNT_{index}_FLANGE_LOAD_SPREADER_PROVISIONAL"]
        web = station[f"MOUNT_{index}_REMOVABLE_BRIDGE_PROVISIONAL"]
        receiver = next(
            item for item in station.values() if "FACTORY_ANCHOR_RECEIVER" in item.label
        )
        _close(pad.center().X, x)
        _close(pad.center().Y, y)
        assert (receiver & anchor).volume > 0.0
        assert (receiver & web).volume > 0.0
        assert (web & pad).volume > 0.0
        matching_flange = flanges[0] if y > 0.0 else flanges[1]
        assert (pad & matching_flange).volume > 0.0

    controls = make_relocated_control_system().children
    assert len(controls) == 8
    assert tuple(value(bed_control_functions)) == ("TONNEAU", "TAILGATE")
    source_keepouts = [
        item for item in make_keep_out_zones().children if "BED_CONTROL" in item.label
    ]
    assert len(source_keepouts) == 2
    for function, keepout in zip(value(bed_control_functions), source_keepouts):
        station = [item for item in controls if item.label.startswith(function)]
        assert len(station) == 4
        source = next(item for item in station if "SOURCE_COUPLER" in item.label)
        vertical = next(item for item in station if "ROUTE_VERTICAL" in item.label)
        lateral = next(item for item in station if "ROUTE_OUTBOARD" in item.label)
        pod = next(item for item in station if "CONTROL_POD" in item.label)
        assert (source & keepout).volume > 0.0
        assert (source & vertical).volume > 0.0
        assert (vertical & lateral).volume > 0.0
        assert (lateral & pod).volume > 0.0
        _close(pod.center().Z, value(relocated_control_pod_height))

    ports = make_topper_crossbar_ports().children
    assert len(ports) == 8
    assert crossbar_interface_width.provenance == PLACEHOLDER_REQUIRING_SCAN
    assert crossbar_interface_depth.provenance == PLACEHOLDER_REQUIRING_SCAN
    shell = make_engineered_shell()
    for station_index, x in enumerate(
        (value(topper_crossbar_station_1), value(topper_crossbar_station_2)),
        start=1,
    ):
        station = [item for item in ports if f"CROSSBAR_{station_index}_" in item.label]
        assert len(station) == 4
        assert {round(abs(item.center().Y), 6) for item in station} == {
            value(crossbar_mount_span) / 2.0
        }
        assert {round(item.center().X, 6) for item in station} == {x}
        for side in ("DRIVER", "PASSENGER"):
            hardpoint = next(
                item
                for item in station
                if side in item.label and "HARDPOINT" in item.label
            )
            port = next(
                item
                for item in station
                if side in item.label and "ACCESSORY_PORT" in item.label
            )
            assert (hardpoint & shell).volume > 0.0
            assert (hardpoint & port).volume > 0.0

    keepouts = make_vehicle_and_service_keepouts().children
    assert len(keepouts) == 11
    assert all("KEEP_OUT" in item.label for item in keepouts)
    assert all(
        PLACEHOLDER_REQUIRING_SCAN.replace(" ", "_") in item.label
        for item in keepouts
    )
    cab = next(item for item in keepouts if "CAB_RELATIVE_MOTION" in item.label)
    tailgate = next(item for item in keepouts if "TAILGATE" in item.label)
    tonneau = next(item for item in keepouts if "TONNEAU" in item.label)
    assert cab.bounding_box().min.X < 0.0 < cab.bounding_box().max.X
    assert tailgate.bounding_box().max.X > value(topper_overall_length)
    assert tailgate.bounding_box().min.Z < 0.0
    _close(tonneau.bounding_box().max.Z, 0.0)

    labels = {child.label for child in build_mount_interface_subassembly().children}
    assert labels == {
        "TOPPER_ENGINEERED_SHELL_BASELINE",
        "QUICK_RELEASE_MOUNT_ADAPTERS",
        "RELOCATED_MECHANICAL_CONTROLS",
        "TOPPER_CROSSBAR_PORT_SYSTEM",
        "VEHICLE_AND_SERVICE_KEEP_OUTS",
    }
if __name__ == "__main__":
    run()
    print("STEP_9_MOUNT_INTERFACE_CHECKS_PASS")
