import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))
from blast_agent import run_scraper

@patch("blast_agent.sys.exit")
@patch("blast_agent.subprocess.run")
def test_run_scraper_success(mock_run, mock_exit, tmp_path):
    # Setup mock exit to raise SystemExit so execution stops
    mock_exit.side_effect = SystemExit(0)

    with patch("blast_agent.WORKSPACE_ROOT", tmp_path):
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        scraper_file = tools_dir / "scraper_test_scraper.py"
        scraper_file.touch()

        mock_run_result = MagicMock()
        mock_run_result.returncode = 0
        mock_run.return_value = mock_run_result

        with pytest.raises(SystemExit):
            run_scraper("test_scraper", ["--arg1", "val1"])

        args, kwargs = mock_run.call_args
        cmd = args[0]
        assert cmd[0] == sys.executable
        assert cmd[1] == str(scraper_file)
        assert cmd[2:] == ["--arg1", "val1"]

        mock_exit.assert_called_once_with(0)

@patch("blast_agent.sys.exit")
@patch("blast_agent.subprocess.run")
def test_run_scraper_opendata_alias(mock_run, mock_exit, tmp_path):
    mock_exit.side_effect = SystemExit(0)

    with patch("blast_agent.WORKSPACE_ROOT", tmp_path):
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        scraper_file = tools_dir / "scraper_opendata_dortmund.py"
        scraper_file.touch()

        mock_run_result = MagicMock()
        mock_run_result.returncode = 0
        mock_run.return_value = mock_run_result

        with pytest.raises(SystemExit):
            run_scraper("opendata", ["--arg1"])

        args, kwargs = mock_run.call_args
        cmd = args[0]
        assert cmd[0] == sys.executable
        assert cmd[1] == str(scraper_file)
        assert cmd[2:] == ["--arg1"]

        mock_exit.assert_called_once_with(0)

@patch("blast_agent.sys.exit")
@patch("blast_agent.subprocess.run")
def test_run_scraper_not_found(mock_run, mock_exit, tmp_path, capsys):
    mock_exit.side_effect = SystemExit(1)

    with patch("blast_agent.WORKSPACE_ROOT", tmp_path):
        with pytest.raises(SystemExit):
            run_scraper("nonexistent", [])

        mock_run.assert_not_called()
        mock_exit.assert_called_once_with(1)

        captured = capsys.readouterr()
        assert "Error: Scraper scraper_nonexistent.py not found." in captured.err
