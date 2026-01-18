"""Tests for logger and output formatting."""

from __future__ import annotations

import json

import pytest

from harness.core.logger import Logger, OutputBuffer, print_json


class TestOutputBuffer:
    """Tests for OutputBuffer class."""

    def test_add_event(self) -> None:
        """Test adding events to buffer."""
        buffer = OutputBuffer()
        buffer.add_event("info", "Test message")

        assert len(buffer.events) == 1
        assert buffer.events[0]["level"] == "info"
        assert buffer.events[0]["message"] == "Test message"

    def test_add_event_with_extra(self) -> None:
        """Test adding events with extra data."""
        buffer = OutputBuffer()
        buffer.add_event("info", "Step complete", step=1, total=5)

        assert buffer.events[0]["step"] == 1
        assert buffer.events[0]["total"] == 5

    def test_set_result(self) -> None:
        """Test setting result data."""
        buffer = OutputBuffer()
        buffer.set_result({"success": True, "count": 3})

        assert buffer.result == {"success": True, "count": 3}

    def test_to_dict(self) -> None:
        """Test converting buffer to dictionary."""
        buffer = OutputBuffer()
        buffer.add_event("info", "Message 1")
        buffer.add_event("success", "Message 2")
        buffer.set_result({"done": True})

        result = buffer.to_dict()

        assert "events" in result
        assert len(result["events"]) == 2
        assert "result" in result
        assert result["result"]["done"] is True

    def test_to_dict_without_result(self) -> None:
        """Test to_dict when no result is set."""
        buffer = OutputBuffer()
        buffer.add_event("info", "Test")

        result = buffer.to_dict()

        assert "events" in result
        assert "result" not in result

    def test_to_json(self) -> None:
        """Test converting buffer to JSON string."""
        buffer = OutputBuffer()
        buffer.add_event("info", "Test message")
        buffer.set_result({"success": True})

        json_str = buffer.to_json()
        parsed = json.loads(json_str)

        assert parsed["events"][0]["message"] == "Test message"
        assert parsed["result"]["success"] is True


class TestLogger:
    """Tests for Logger class."""

    def test_json_mode_disabled_by_default(self) -> None:
        """Test that JSON mode is off by default."""
        logger = Logger()

        assert logger.json_mode is False

    def test_json_mode_can_be_enabled(self) -> None:
        """Test enabling JSON mode."""
        logger = Logger(json_mode=True)

        assert logger.json_mode is True

    def test_json_mode_setter(self) -> None:
        """Test setting JSON mode after creation."""
        logger = Logger()
        logger.json_mode = True

        assert logger.json_mode is True

    def test_json_mode_buffers_info(self) -> None:
        """Test that info messages are buffered in JSON mode."""
        logger = Logger(json_mode=True)
        logger.info("Test info message")

        buffer = logger.get_buffer()
        assert len(buffer.events) == 1
        assert buffer.events[0]["level"] == "info"
        assert buffer.events[0]["message"] == "Test info message"

    def test_json_mode_buffers_success(self) -> None:
        """Test that success messages are buffered in JSON mode."""
        logger = Logger(json_mode=True)
        logger.success("Operation complete")

        buffer = logger.get_buffer()
        assert buffer.events[0]["level"] == "success"

    def test_json_mode_buffers_warning(self) -> None:
        """Test that warning messages are buffered in JSON mode."""
        logger = Logger(json_mode=True)
        logger.warn("Warning message")

        buffer = logger.get_buffer()
        assert buffer.events[0]["level"] == "warning"

    def test_json_mode_buffers_error(self) -> None:
        """Test that error messages are buffered in JSON mode."""
        logger = Logger(json_mode=True)
        logger.error("Error occurred")

        buffer = logger.get_buffer()
        assert buffer.events[0]["level"] == "error"

    def test_json_mode_buffers_header(self) -> None:
        """Test that headers are buffered in JSON mode."""
        logger = Logger(json_mode=True)
        logger.header("Section Title")

        buffer = logger.get_buffer()
        assert buffer.events[0]["level"] == "header"
        assert buffer.events[0]["message"] == "Section Title"

    def test_json_mode_buffers_step(self) -> None:
        """Test that steps are buffered with step info."""
        logger = Logger(json_mode=True)
        logger.step(2, 5, "Processing")

        buffer = logger.get_buffer()
        assert buffer.events[0]["step"] == 2
        assert buffer.events[0]["total"] == 5

    def test_json_mode_buffers_bullet(self) -> None:
        """Test that bullets are buffered as details."""
        logger = Logger(json_mode=True)
        logger.bullet("Item detail")

        buffer = logger.get_buffer()
        assert buffer.events[0]["level"] == "detail"

    def test_set_result(self) -> None:
        """Test setting result data."""
        logger = Logger(json_mode=True)
        logger.set_result({"vms": 3, "success": True})

        buffer = logger.get_buffer()
        assert buffer.result == {"vms": 3, "success": True}

    def test_flush_json_clears_buffer(self, capsys: pytest.CaptureFixture) -> None:
        """Test that flush_json outputs and clears buffer."""
        logger = Logger(json_mode=True)
        logger.info("Test message")
        logger.set_result({"done": True})

        logger.flush_json()

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["events"][0]["message"] == "Test message"
        assert output["result"]["done"] is True

        # Buffer should be cleared
        assert len(logger.get_buffer().events) == 0

    def test_info_with_extra_data(self) -> None:
        """Test passing extra data to info."""
        logger = Logger(json_mode=True)
        logger.info("VM created", vm_id=200, name="test-vm")

        buffer = logger.get_buffer()
        assert buffer.events[0]["vm_id"] == 200
        assert buffer.events[0]["name"] == "test-vm"


class TestPrintJson:
    """Tests for print_json function."""

    def test_print_dict(self, capsys: pytest.CaptureFixture) -> None:
        """Test printing a dictionary."""
        print_json({"key": "value", "number": 42})

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["key"] == "value"
        assert output["number"] == 42

    def test_print_with_indent(self, capsys: pytest.CaptureFixture) -> None:
        """Test printing with custom indent."""
        print_json({"key": "value"}, indent=4)

        captured = capsys.readouterr()
        # Check it's properly indented (4 spaces)
        assert '    "key"' in captured.out

    def test_print_compact(self, capsys: pytest.CaptureFixture) -> None:
        """Test printing without indent (compact)."""
        print_json({"key": "value"}, indent=None)

        captured = capsys.readouterr()
        # Should be on one line
        assert "\n" not in captured.out.strip()
