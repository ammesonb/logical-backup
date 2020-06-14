"""
Check device functions
"""

from logical_backup.objects.device import Device


def test_equality():
    """
    Check getter/setter and compare functions
    """
    name = "foo"
    path = "/test/foo"
    identifier_type = "Stuff"
    identifier_type_id = 5
    identifier = "12345"

    device = Device()
    device.set(name, path, identifier_type, identifier, identifier_type_id)
    assert device.device_name == name, "Device name should match"
    assert device.device_path == path, "Device path should match"
    assert device.identifier == identifier, "Device identifier should match"
    assert (
        device.identifier_type == identifier_type
    ), "Device identifier type should match"
    assert (
        device.identifier_type_id == identifier_type_id
    ), "Device identifier type ID should match"

    assert device == {
        "device_name": name,
        "device_path": path,
        "identifier": identifier,
        "identifier_type": identifier_type,
        "identifier_type_id": identifier_type_id,
    }, "Device should equal dict"

    assert device != {
        "device_name": name,
        "device_path": path,
        "identifier": identifier,
        "identifier_type": identifier_type,
        "identifier_type_id": 4,
    }, "Device should NOT equal dict"

    device2 = Device()
    device2.set(name, path, identifier_type, identifier, identifier_type_id)

    assert device == device2, "Two devices should match"
    device.identifier_type = "Garbage"
    assert device != device2, "Devices should NOT match"
