import pytest

from game_objects.frame import Frame


@pytest.mark.asyncio
def test_arc(load_image):
    f = Frame.strip(load_image("test_00145.png"))
    arc_pos = f.arc_pos
    assert arc_pos == ((96, 141), (398, 256))

    # save_image("arc_pos.png", f.crop(arc_pos))


@pytest.mark.asyncio
def test_score(load_image):
    f = Frame.strip(load_image("test_00145.png"))
    score_pos = f.score_pos
    assert score_pos == ((0, 0), (83, 398))

    # save_image("score_pos.png", f.crop(score_pos))


@pytest.mark.asyncio
def test_left_screen(load_image):
    f = Frame.strip(load_image("test_00145.png"))

    assert (f.left_screen_pos, f.right_screen_pos) == (
        ((96, 0), (416, 141)),
        ((96, 256), (416, 398)),
    )

    # save_image("screenl.png", f.crop(screen))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "img_name,expected",
    [
        ("game_started_multi.png", ([0, 0, 0], [0, 0, 0])),
        ("game_started_solo.png", ([0, 0, 9], [None, None, None])),
        ("test_00145.png", ([19, 0, 0], [8, 1, 0])),
        ("test_00164.png", ([27, 0, 0], [10, 1, 0])),
        ("game_over_right.png", ([121, 0, 0], [243, 0, 0])),
        ("game_over_both.png", ([242, 0, 0], [243, 0, 0])),
        ("game_over_solo.png", ([129, 0, 0], [None, None, None])),
        ("test_dance.png", ([1314, 31, 1], [426, 15, 0])),
    ],
)
def test_score_frame(img_name, expected, refs, load_image):
    f = Frame.strip(load_image(img_name))
    score_frame = f.get_score_frame()
    l, r = score_frame.get_sides(refs)

    # save_image("screenl.png", f.crop(l))
    # save_image("screenr.png", f.crop(r))

    # ll = l.lines_stripped()
    # rl = r.lines_stripped()

    # save_image("l1.png", l.crop(ll[0]))
    # save_image("l2.png", l.crop(ll[1]))
    # save_image("l3.png", l.crop(ll[2]))

    # save_image("r1.png", r.crop(rl[0]))
    # save_image("r2.png", r.crop(rl[1]))
    # save_image("r3.png", r.crop(rl[2]))

    lt = [l.get_line(i) for i in range(3)]
    rt = [r.get_line(i) for i in range(3)]
    assert (lt, rt) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "img_name,expected",
    [
        ("game_started_multi.png", False),
        ("game_started_solo.png", False),
        ("test_00145.png", False),
        ("test_00164.png", False),
        ("test_00171.png", False),
        ("test_00329.png", False),
        ("test_00330.png", False),
        ("test_00577.png", False),
        ("game_over_both.png", False),
        ("game_over_solo.png", False),
        ("test_dance.png", False),
        ("menu.png", False),
        ("menu2.png", False),
        ("pause.png", True),
    ],
)
def test_is_paused(img_name, expected, load_image):
    f = Frame.strip(load_image(img_name))
    assert f.is_paused == expected


@pytest.mark.asyncio
def test_menu(load_image):
    f = Frame.strip(load_image("menu.png"))
    assert not f.is_paused
    sides = f.get_score_frame().get_sides
    assert sides
    assert not f.is_game


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "img_name,expected",
    [
        ("game_started_multi.png", True),
        ("game_started_solo.png", True),
        ("test_00145.png", True),
        ("test_00164.png", True),
        ("game_over_both.png", True),
        ("game_over_solo.png", True),
        ("test_dance.png", True),
        ("menu.png", False),
        ("menu2.png", False),
    ],
)
def test_menu2(img_name, expected, load_image):
    f = Frame.strip(load_image(img_name))
    assert f.is_game == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "img_name,expected",
    [
        ("game_started_multi.png", (False, False)),
        ("game_started_solo.png", (False, False)),
        ("test_00145.png", (False, False)),
        ("test_00164.png", (False, False)),
        ("test_00329.png", (False, False)),
        ("test_00330.png", (False, False)),
        ("test_00577.png", (False, False)),
        ("game_over_both.png", (True, True)),
        ("game_over_solo.png", (True, False)),
        ("game_over_right.png", (False, True)),
        ("test_dance.png", (False, False)),
        ("menu.png", (False, False)),
        ("pause.png", (False, False)),
    ],
)
def test_game_over(img_name, expected, load_image, refs):
    f = Frame.strip(load_image(img_name))
    screens = f.get_player_screens(refs)
    assert (screens[0].is_game_over, screens[1].is_game_over) == expected
