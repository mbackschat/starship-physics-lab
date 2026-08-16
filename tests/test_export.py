"""Writing a study's results next to the study, and nowhere else.

`labbook.export` had no tests. It is small, but it decides where every generated
figure and table in the repository lands, and it used to carry a module-level
default pointing at a shared `studies/out`. Nothing ever used that default; it
existed only as a way to write outside the folder holding the script and its
finding, which is the one thing the studies convention forbids.
"""


import pytest

import labbook
from labbook.export import beside, save_data, save_table


class TestWhereOutputGoes:
    def test_beside_returns_the_out_directory_next_to_a_script(self, tmp_path):
        run = tmp_path / "my-question" / "run.py"
        # Resolved, so a symlinked temp directory compares equal on macOS.
        assert beside(str(run)) == (run.parent / "out").resolve()

    def test_beside_does_not_create_anything_by_itself(self, tmp_path):
        target = beside(str(tmp_path / "run.py"))
        assert not target.exists()

    def test_saving_creates_the_directory(self, tmp_path):
        target = tmp_path / "out"
        written = save_table("| a |\n| - |\n", "table", out_dir=target)
        assert written == target / "table.md"
        assert written.read_text().endswith("\n")

    def test_a_study_writes_into_its_own_folder(self, tmp_path):
        run = tmp_path / "my-question" / "run.py"
        run.parent.mkdir(parents=True)
        written = save_table("x", "answer", out_dir=beside(str(run)))
        assert written.parent == run.parent / "out"


class TestTheDestinationIsRequired:
    """The convention, enforced rather than remembered.

    CLAUDE.md says to write output with `beside(__file__)`. A default made that
    advice rather than a rule, and advice is not checkable.
    """

    def test_the_module_offers_no_default_destination(self):
        assert not hasattr(labbook, "OUT_DIR")
        assert "OUT_DIR" not in labbook.__all__

    def test_save_table_will_not_guess(self):
        with pytest.raises(TypeError, match="out_dir"):
            save_table("x", "name")  # type: ignore[call-arg]

    def test_save_data_will_not_guess(self):
        with pytest.raises(TypeError, match="out_dir"):
            save_data([{"a": 1}], "name")  # type: ignore[call-arg]

    def test_save_figure_will_not_guess(self):
        import plotly.graph_objects as go

        from labbook.export import save_figure

        with pytest.raises(TypeError, match="out_dir"):
            save_figure(go.Figure(), "name")  # type: ignore[call-arg]


class TestSaveData:
    def test_it_writes_a_header_and_the_rows(self, tmp_path):
        path = save_data([{"name": "Falcon 9", "payload": 17.5}], "d", out_dir=tmp_path)
        assert path.read_text().splitlines()[0] == "name,payload"

    def test_nothing_to_write_is_refused_rather_than_leaving_an_empty_file(self, tmp_path):
        with pytest.raises(ValueError, match="nothing to write"):
            save_data([], "d", out_dir=tmp_path)
        assert list(tmp_path.iterdir()) == []
