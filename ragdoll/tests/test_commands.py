from maya import cmds
from .. import commands, constants
from ..vendor import cmdx
from ..tools import chain_tool
from . import _play, _new, _step

from nose.tools import (
    assert_equals,
    assert_almost_equals,
)


def test_defaults():
    _new()

    cube, _ = cmds.polyCube()
    cube = cmdx.encode(cube)  # Convert to cmdx
    cube["translateY"] = 10
    cube["rotate", cmdx.Degrees] = (35, 50, 30)

    cmds.currentTime(1)

    scene = commands.create_scene()
    commands.create_rigid(cube, scene)

    for frame in range(1, 30):
        cube["ty"].read()  # Trigger evaluation
        cmds.currentTime(frame)

    # It'll be resting on the ground at this point
    assert_almost_equals(cube["ty"].read(), 0.500, 3)


def test_delete_all():
    _new()

    a = cmdx.createNode("transform")
    b = cmdx.createNode("transform", parent=a)
    c = cmdx.createNode("transform", parent=b)
    d = cmdx.createNode("transform", parent=c)

    a["ty"] = 5.0
    b["tx"] = 5.0
    c["tx"] = 5.0
    d["tx"] = 5.0

    scene = commands.create_scene()

    operator = chain_tool.Chain([a, b, c, d], scene)
    assert operator.pre_flight()
    operator.do_it()
    assert_equals(len(cmds.ls(type="rdRigid")), 4)

    result = commands.delete_physics([scene, a, b, c, d])

    # 1 scene, 4 rigids, 3 constraints, 1 multiplier
    assert_equals(result["deletedRagdollNodeCount"], 9)

    # Scene node transform
    assert_equals(result["deletedExclusiveNodeCount"], 1)

    assert_equals(len(cmds.ls(type="rdRigid")), 0)

    cmds.undo()

    assert_equals(len(cmds.ls(type="rdRigid")), 4)

    commands.delete_physics([a, b, c, d])
    assert_equals(len(cmds.ls(type="rdRigid")), 0)


def test_convert_constraint():
    pass


def test_convert_rigid():
    # Passive -> Active
    # Active -> Passive
    pass


def manual():
    import sys
    import time

    t0 = time.time()

    mod = sys.modules[__name__]
    tests = list(
        func
        for name, func in mod.__dict__.items()
        if name.startswith("test_")
    )

    errors = []
    for test in tests:
        test()

    # Cleanup
    _new()
    t1 = time.time()
    duration = t1 - t0

    if not errors:
        print("Successfully ran %d tests in %.2fs" % (len(tests), duration))
    else:
        print("Ran %d tests with %d errors in %.2fs" % (
            len(tests), len(errors), duration)
        )


def test_chain_tree_tiger():
    # "simulated" attribute only appears on tree root
    # multiplier applies to
    pass


def test_save_load_tiger():
    # Animation/initial pose should not be affected by saving/loading
    pass


def test_scene_clean():
    """rdScene.clean accurately tells us whether it has been evaluated"""

    _new()

    parent = cmdx.create_node("transform", name="parent")
    child = cmdx.create_node("transform", name="child", parent=parent)

    scene = commands.create_scene()
    commands.create_rigid(child, scene)

    # Trigger evaluation
    child["translateX"].read()
    assert not scene["clean"].read()

    def part_of_scene(transform, scene):
        """We'll know whether `transform` is involved via scene.clean"""
        scene["clean"] = True
        transform["translateX"].read()
        return not scene["clean"].read()

    assert part_of_scene(child, scene), (
        "%s should have been part of scene" % child
    )

    assert not part_of_scene(parent, scene), (
        "%s should NOT have been part of scene" % parent
    )


def test_scene_clean_passive():
    """rdScene.clean understands active versus passive rigids"""

    _new()

    parent = cmdx.create_node("transform", name="parent")
    child = cmdx.create_node("transform", name="child", parent=parent)

    scene = commands.create_scene()

    commands.create_rigid(parent, scene, opts={"passive": True})
    commands.create_rigid(child, scene, opts={"passive": False})

    # Trigger evaluation
    child["translateX"].read()
    assert not scene["clean"].read()

    def part_of_scene(transform, scene):
        """We'll know whether `transform` is involved via scene.clean"""
        scene["clean"] = True
        transform["translateX"].read()
        return not scene["clean"].read()

    assert part_of_scene(child, scene), (
        "%s should have been part of scene" % child
    )

    assert not part_of_scene(parent, scene), (
        "%s should NOT have been part of scene" % parent
    )


def test_rotate_pivot():
    assert True


def test_rotate_order():
    assert True


def test_rotate_axis():
    assert True


def test_joint_orient():
    assert True


def test_animation_constraint_1():
    """Animation constraint to passive parent"""

    _new(1, 120)

    a = cmdx.createNode("transform")
    b = cmdx.createNode("transform", parent=a)

    a["ty"] = 5.0
    b["tx"] = 5.0

    scene = commands.create_scene()
    scene["gravity"] = 0

    commands.create_rigid(a, scene, opts={"passive": True})
    rb = commands.create_rigid(b, scene)

    commands.animation_constraint(rb)

    assert_almost_equals(a.translation(cmdx.sWorld).y, 5.0, 2)
    assert_almost_equals(b.translation(cmdx.sWorld).y, 5.0, 2)

    _step(b, 3)

    assert_almost_equals(a.translation(cmdx.sWorld).y, 5.0, 2)
    assert_almost_equals(b.translation(cmdx.sWorld).y, 5.0, 2)

    a["ty"] = 10.0

    _step(b, 100)

    assert_almost_equals(a.translation(cmdx.sWorld).y, 10.0, 2)
    assert_almost_equals(b.translation(cmdx.sWorld).y, 10.0, 2)


def test_animation_constraint_2():
    """Animation constraint to dynamic parent"""

    _new(1, 120)

    a = cmdx.createNode("transform")
    b = cmdx.createNode("transform", parent=a)

    a["ty"] = 5.0
    b["tx"] = 5.0

    scene = commands.create_scene()
    scene["gravity"] = 0

    ra = commands.create_rigid(a, scene)
    rb = commands.create_rigid(b, scene)

    commands.animation_constraint(ra)
    commands.animation_constraint(rb)

    assert_almost_equals(a.translation(cmdx.sWorld).y, 5.0, 2)
    assert_almost_equals(b.translation(cmdx.sWorld).y, 5.0, 2)

    _step(b, 3)

    assert_almost_equals(a.translation(cmdx.sWorld).y, 5.0, 2)
    assert_almost_equals(b.translation(cmdx.sWorld).y, 5.0, 2)

    pb = a["tx"].connection(type="pairBlend")
    pb["inTranslateY1"] = {1: 10.0}  # Keyframe it

    _step(b, 100)

    assert_almost_equals(a.translation(cmdx.sWorld).y, 10.0, 2)
    assert_almost_equals(b.translation(cmdx.sWorld).y, 10.0, 2)


def test_animation_constraint_3():
    """Animation constraint to kinematic parent"""

    _new(1, 120)

    a = cmdx.createNode("transform")
    b = cmdx.createNode("transform", parent=a)

    a["ty"] = 5.0
    b["tx"] = 5.0

    scene = commands.create_scene()
    scene["gravity"] = 0

    rb = commands.create_rigid(b, scene)

    commands.animation_constraint(rb)

    assert_almost_equals(a.translation(cmdx.sWorld).y, 5.0, 2)
    assert_almost_equals(b.translation(cmdx.sWorld).y, 5.0, 2)

    _step(b, 3)

    assert_almost_equals(a.translation(cmdx.sWorld).y, 5.0, 2)
    assert_almost_equals(b.translation(cmdx.sWorld).y, 5.0, 2)

    a["ty"] = 10.0

    _step(b, 100)

    assert_almost_equals(a.translation(cmdx.sWorld).y, 10.0, 2)
    assert_almost_equals(b.translation(cmdx.sWorld).y, 10.0, 2)


if cmdx.__maya_version__ >= 2019:
    def test_up_axes():
        """Both Z and Y-up axes behave as you would expect"""

        def new(axis):
            _new()
            cmdx.setUpAxis(axis)
            box, _ = map(cmdx.encode, cmds.polyCube())
            box["translateY"] = 10
            box["translateZ"] = 10

            scene = commands.create_scene()
            rigid = commands.create_rigid(box, scene)
            rigid["shapeType"] = constants.BoxShape
            rigid["shapeExtents"] = (1, 1, 1)
            return rigid

        rigid = new(cmdx.Y)
        _play(rigid, start=1, end=50)
        assert_almost_equals(rigid["outputTranslateY"].read(), 0.5, 2)

        # It may bounce around a little, that's OK
        assert_almost_equals(rigid["outputTranslateZ"].read(), 10.0, 1)

        # Test Z
        rigid = new(cmdx.Z)
        _play(rigid, start=1, end=50)
        assert_almost_equals(rigid["outputTranslateY"].read(), 10.0, 1)
        assert_almost_equals(rigid["outputTranslateZ"].read(), 0.5, 2)
