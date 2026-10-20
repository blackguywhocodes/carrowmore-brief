"""The rules worth keeping if this graduated. Run: python -m unittest"""

import unittest
from pathlib import Path

from carrowmore.claims import has_done
from carrowmore.model import Action, Claim, ClaimKind, Depth, Evidence, EvidenceError, Role, Step
from carrowmore.route import RouteError, check, order
from carrowmore.skills import classify

PACK = Path(__file__).resolve().parent.parent / "carrowmore-data-pack"


def ev(role: Role, depth: Depth = Depth.SKILLED, year: int = 2020, i: int = 0) -> Evidence:
    return Evidence(f"CL{i:06d}", f"{year}-01-01", "Test Rock", "raw/x.txt#L1", "text", role, depth)


class ClaimInvariants(unittest.TestCase):
    def test_has_done_without_evidence_is_refused(self):
        with self.assertRaises(EvidenceError):
            Claim("K0001", "hv_switching", ClaimKind.HAS_DONE, "Has done it.")

    def test_standing_by_never_counts_as_doing(self):
        role, skills = classify("Stood by while the AK switched the no.2 transformer out.")
        self.assertIs(role, Role.OBSERVED)
        self.assertIn("hv_switching", skills)
        observed = [ev(Role.OBSERVED, i=i, year=2015 + i) for i in range(6)]
        self.assertIsNone(has_done("K0001", "hv_switching", observed))

    def test_strength_needs_spread_and_recency(self):
        five_in_one_year = [ev(Role.PERFORMED, i=i) for i in range(5)]
        self.assertEqual(has_done("K0001", "boat", five_in_one_year).strength.value, "moderate")
        old = [ev(Role.PERFORMED, i=i, year=1990 + i) for i in range(6)]
        claim = has_done("K0001", "boat", old)
        self.assertEqual(claim.strength.value, "moderate")
        self.assertIn("nothing since 1995", claim.text)

    def test_step_needs_an_action(self):
        with self.assertRaises(ValueError):
            Step("x", "book", "Book something.")


class RuleRegressions(unittest.TestCase):
    """Each of these was a real misfire in the first draft of the rules."""

    def test_refused_is_not_a_fuse(self):
        _, skills = classify("Reported the landing as unsafe and refused relief until it was made good.")
        self.assertNotIn("electrical", skills)

    def test_showed_when_is_not_teaching(self):
        role, skills = classify("Fault only showed when the compressor cut in, proved it with the clamp meter.")
        self.assertIs(role, Role.PERFORMED)
        self.assertNotIn("training_others", skills)

    def test_permit_book_numbers_still_match(self):
        _, skills = classify(
            "Racked out no.2 breaker, locked off, caps on, danger notices up. Permit bk.3 no.41 refers."
        )
        self.assertIn("permits", skills)

    def test_disciplinary_entries_are_excluded(self):
        self.assertIsNone(
            classify("Had to stand a man down for coming back unfit. Reported it and dealt with it on station.")
        )


class RouteInvariants(unittest.TestCase):
    def test_prerequisites_come_first(self):
        steps = [Step(k, Action.BOOK, k) for k in ("WAHS-2", "OSSC-SS", "medical", "HVAP-01", "MECS-3")]
        steps += [Step("interest", Action.ASK, "x"), Step("HV-paperwork", Action.FETCH, "x")]
        route = order(steps)
        keys = [s.key for s in route]
        self.assertEqual(keys[0], "interest")
        self.assertLess(keys.index("medical"), keys.index("OSSC-SS"))
        self.assertLess(keys.index("OSSC-SS"), keys.index("WAHS-2"))
        self.assertLess(keys.index("MECS-3"), keys.index("HVAP-01"))
        self.assertLess(keys.index("HV-paperwork"), keys.index("HVAP-01"))

    def test_check_rejects_a_bad_order(self):
        with self.assertRaises(RouteError):
            check([Step("WAHS-2", Action.BOOK, "x"), Step("OSSC-SS", Action.BOOK, "x")])


@unittest.skipUnless(PACK.exists(), "data pack not present")
class WholeRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from carrowmore.pipeline import run

        cls.results, cls.leavers, cls.facts = run(PACK)
        cls.by_code = {r.keeper.code: r for r in cls.results}

    def test_every_route_respects_prerequisites(self):
        for r in self.results:
            for f in r.fits.values():
                check(f.route)

    def test_every_cited_entry_belongs_to_the_keeper(self):
        for r in self.results:
            own = {e.entry_id for es in r.evidence.values() for e in es}
            for c in r.claims:
                self.assertTrue({e.entry_id for e in c.evidence} <= own)

    def test_k0147_hvap_is_not_current_whatever_the_pack_block_says(self):
        hvap = self.by_code["K0147"].schemes["HVAP"]
        self.assertFalse(hvap.current)
        self.assertEqual([m.code for m in hvap.missing], ["HVAP-01", "HVAP-03"])

    def test_casualty_text_is_never_rendered(self):
        from carrowmore.render import to_json

        data = to_json(self.results, self.leavers, self.facts)
        for k in data["keepers"]:
            for c in k["claims"]:
                if c["subject"] == "first_aid":
                    self.assertTrue(all(e["text"] is None for e in c["evidence"]))

    def test_leavers_are_not_assessed(self):
        self.assertTrue(all(r.keeper.current for r in self.results))


if __name__ == "__main__":
    unittest.main()
