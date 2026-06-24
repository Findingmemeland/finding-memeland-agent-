from finding_memeland.content.clue_engine import (
    PersonaContext,
    clue_plan,
    clue_vector_for,
    guidance_for,
    shuffled_facet_plan,
)


def _persona(name):
    return PersonaContext(
        display_name=name, handle="@x", bio="b", avatar_description="a",
        voice="v", backstory="bs", solution_terms=["secret"],
        banner_description="banner", findable_post="a very distinctive phrase here",
    )


def test_single_word_name_has_one_name_facet():
    plan = clue_plan(_persona("icarus"))
    assert "name_word_1" in plan and "name_word_2" not in plan


def test_two_word_name_has_two_name_facets():
    plan = clue_plan(_persona("Celestial Mechanic"))
    assert "name_word_1" in plan and "name_word_2" in plan and "name_word_3" not in plan


def test_three_word_name_has_a_facet_for_every_word():
    # The whole point of this change: 3 words -> 3 name clues, not just first+last.
    plan = clue_plan(_persona("Arachne Spinnerette Weaver"))
    assert {"name_word_1", "name_word_2", "name_word_3"} <= set(plan)


def test_guidance_resolves_each_name_word_to_the_right_word():
    p = _persona("Arachne Spinnerette Weaver")
    assert "Arachne" in guidance_for("name_word_1", p)
    assert "Spinnerette" in guidance_for("name_word_2", p)
    assert "Weaver" in guidance_for("name_word_3", p)


def test_ordered_fallback_plan():
    p = _persona("Celestial Mechanic")
    assert clue_plan(p) == ["name_word_1", "name_word_2", "avatar", "banner", "bio", "signature_post"]
    assert clue_vector_for(len(clue_plan(p)), p) == "signature_post"


def test_shuffled_plan_always_ends_in_signature_post():
    for _ in range(50):
        plan = shuffled_facet_plan("Arachne Spinnerette Weaver")
        assert plan[-1] == "signature_post"
        assert "signature_post" not in plan[:-1]


def test_shuffled_plan_contains_all_facets_three_word_name():
    plan = shuffled_facet_plan("Arachne Spinnerette Weaver")
    assert set(plan) == {
        "name_word_1", "name_word_2", "name_word_3", "avatar", "banner", "bio", "signature_post",
    }


def test_order_actually_varies_across_hunts():
    plans = {tuple(shuffled_facet_plan("Celestial Mechanic")) for _ in range(30)}
    assert len(plans) > 1


def test_late_clues_clamp_to_locator_post():
    plan = shuffled_facet_plan("icarus")
    p = _persona("icarus")
    p.clue_facet_plan = plan
    assert clue_vector_for(len(plan), p) == "signature_post"
    assert clue_vector_for(len(plan) + 5, p) == "signature_post"


def test_every_planned_facet_has_resolvable_guidance():
    p = _persona("Arachne Spinnerette Weaver")
    for facet in clue_plan(p):
        assert guidance_for(facet, p)  # non-empty, no KeyError
