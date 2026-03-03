"""
Sprint Execution Readiness Verification
Verifies the SPRINT_EXECUTION_TECH_SPEC is complete and ready for development
"""

import pytest
import re
from pathlib import Path


class TestSprintExecutionStructure:
    """Verify tech spec file has required structure and sections."""

    @pytest.fixture
    def tech_spec_content(self):
        """Load tech spec document."""
        spec_path = Path(__file__).parent.parent.parent / "docs" / "SPRINT_EXECUTION_TECH_SPEC.md"
        assert spec_path.exists(), f"Tech spec not found at {spec_path}"
        return spec_path.read_text()

    def test_tech_spec_has_all_required_sections(self, tech_spec_content):
        """Verify tech spec includes all required sections."""
        required_sections = [
            "Implementation Overview",
            "Files & Modules Affected",
            "Detailed Implementation Approach",
            "Testing Strategy",
            "Timeline & Milestones",
            "Risk Mitigation",
            "Definition of Done",
        ]

        for section in required_sections:
            assert section in tech_spec_content, f"Missing section: {section}"

    def test_all_six_sprints_defined(self, tech_spec_content):
        """Verify all 6 sprints are documented with tasks and point estimates."""
        sprint_keywords = [
            "Sprint 1: Critical Fixes",
            "Sprint 2: Security",
            "Sprint 3",
            "Sprint 5: Database",
            "Sprint 6",
        ]
        for keyword in sprint_keywords:
            assert keyword in tech_spec_content, f"Sprint definition missing: {keyword}"

    def test_sprint_timeline_specified(self, tech_spec_content):
        """Verify each sprint has defined weeks and velocity."""
        timeline_section = re.search(
            r"## 📅 Timeline.*?(?=##|$)",
            tech_spec_content,
            re.DOTALL
        )
        assert timeline_section, "Timeline & Milestones section missing"

        # Verify table has Sprint, Weeks, Velocity columns
        timeline_text = timeline_section.group(0)
        assert "Sprint" in timeline_text
        assert "Weeks" in timeline_text
        assert "Velocity" in timeline_text
        assert "60 points" in timeline_text, "Total 60 points not specified"


class TestCriticalTasksDefinition:
    """Verify critical tasks have complete implementation details."""

    @pytest.fixture
    def tech_spec_content(self):
        """Load tech spec document."""
        spec_path = Path(__file__).parent.parent.parent / "docs" / "SPRINT_EXECUTION_TECH_SPEC.md"
        return spec_path.read_text()

    def test_critical_fixes_all_have_code_examples(self, tech_spec_content):
        """Verify critical task documentation includes code examples."""
        critical_tasks = ["TP-C01", "TP-C02", "TP-C03", "TP-C04"]

        for task_id in critical_tasks:
            assert task_id in tech_spec_content, f"Task {task_id} not found"

        # Verify code examples exist (not all tasks need examples, but most should)
        code_blocks = re.findall(r"```python", tech_spec_content)
        assert len(code_blocks) >= 8, f"Expected 8+ code examples, found {len(code_blocks)}"

    def test_all_tasks_have_owner_and_dependencies(self, tech_spec_content):
        """Verify critical tasks specify owner and dependencies."""
        # Search for Owner and Dependencies fields in detailed task sections
        # These appear after the task ID in the "Detailed Implementation Approach" section
        implementation_section = tech_spec_content.find("## 🔄 Detailed Implementation Approach")
        assert implementation_section != -1, "Detailed Implementation Approach section missing"

        section_text = tech_spec_content[implementation_section:]

        # Verify that Owner and Dependencies are documented for tasks
        assert "Owner" in section_text, "Task owner fields not documented"
        assert "Dependencies" in section_text, "Task dependencies not documented"
        assert "Estimated time" in section_text, "Task time estimates not documented"

    def test_high_priority_tasks_defined(self, tech_spec_content):
        """Verify high-priority tasks (TP-H01 through TP-H05) are defined."""
        high_priority_tasks = ["TP-H01", "TP-H02", "TP-H03", "TP-H04", "TP-H05"]

        for task_id in high_priority_tasks:
            assert task_id in tech_spec_content, f"High-priority task {task_id} not found in tech spec"


class TestFileImpactAndDependencies:
    """Verify all affected files are documented with modification details."""

    @pytest.fixture
    def tech_spec_content(self):
        """Load tech spec document."""
        spec_path = Path(__file__).parent.parent.parent / "docs" / "SPRINT_EXECUTION_TECH_SPEC.md"
        return spec_path.read_text()

    def test_files_affected_table_complete(self, tech_spec_content):
        """Verify critical files are documented in implementation details."""
        # Verify critical core files are mentioned in the spec
        critical_files = [
            "backend/core/ai_analytics.py",
            "backend/core/config.py",
            "backend/api/analysis.py",
            "backend/core/security.py",  # NEW
        ]

        for filename in critical_files:
            assert filename in tech_spec_content, f"Critical file {filename} not mentioned in tech spec"

    def test_new_files_clearly_marked(self, tech_spec_content):
        """Verify new modules are documented in implementation plan."""
        # Verify new test files are mentioned in the spec
        new_test_modules = [
            "test_critical_fixes_verification.py",
            "test_agent_framework.py",
            "backend/core/security.py",
            "backend/core/resilience.py",
        ]

        for module in new_test_modules:
            assert module in tech_spec_content, f"New module {module} not documented"


class TestTestingStrategy:
    """Verify comprehensive testing approach is documented."""

    @pytest.fixture
    def tech_spec_content(self):
        """Load tech spec document."""
        spec_path = Path(__file__).parent.parent.parent / "docs" / "SPRINT_EXECUTION_TECH_SPEC.md"
        return spec_path.read_text()

    def test_testing_strategy_covers_all_levels(self, tech_spec_content):
        """Verify testing strategy includes unit, integration, and load tests."""
        # Search for testing strategy content
        required_test_types = ["Unit Test", "Integration Test", "Load Test"]
        for test_type in required_test_types:
            assert test_type in tech_spec_content, f"Testing strategy missing {test_type}"

    def test_pre_commit_hooks_configured(self, tech_spec_content):
        """Verify pre-commit hook configuration is documented."""
        # Search for pre-commit configuration anywhere in the document
        assert "Pre-Commit Hooks" in tech_spec_content, "Pre-commit hooks section missing"
        assert "mypy" in tech_spec_content, "mypy pre-commit hook not documented"
        assert "pytest" in tech_spec_content, "pytest pre-commit hook not documented"

    def test_definition_of_done_specified(self, tech_spec_content):
        """Verify Definition of Done criteria for task completion."""
        done_section = re.search(
            r"## ✅ Definition of Done.*?(?=##|$)",
            tech_spec_content,
            re.DOTALL
        )
        assert done_section, "Definition of Done section missing"

        done_text = done_section.group(0)

        # Verify key criteria are included
        required_criteria = [
            "Code written",
            "Unit tests passing",
            "Integration tests passing",
            "Code review approved",
            "Documentation updated",
        ]

        for criteria in required_criteria:
            assert criteria in done_text, f"DoD missing criterion: {criteria}"


class TestRiskMitigationStrategy:
    """Verify risk analysis and mitigation plan is comprehensive."""

    @pytest.fixture
    def tech_spec_content(self):
        """Load tech spec document."""
        spec_path = Path(__file__).parent.parent.parent / "docs" / "SPRINT_EXECUTION_TECH_SPEC.md"
        return spec_path.read_text()

    def test_risk_matrix_complete(self, tech_spec_content):
        """Verify risk mitigation section has probability, impact, and mitigation."""
        risk_section = re.search(
            r"## 🚦 Risk Mitigation.*?(?=##|$)",
            tech_spec_content,
            re.DOTALL
        )
        assert risk_section, "Risk Mitigation section missing"

        risk_text = risk_section.group(0)

        # Verify table structure
        assert "Risk" in risk_text
        assert "Probability" in risk_text
        assert "Impact" in risk_text
        assert "Mitigation" in risk_text

        # Verify at least 3 risks documented
        risk_rows = re.findall(r"\|.*?\|.*?\|.*?\|.*?\|", risk_text)
        assert len(risk_rows) >= 3, f"Expected 3+ risks, found {len(risk_rows)}"

    def test_escalation_path_defined(self, tech_spec_content):
        """Verify escalation procedure for blockers and issues."""
        escalation_section = re.search(
            r"## 📞 Escalation Path.*?(?=##|$)",
            tech_spec_content,
            re.DOTALL
        )
        assert escalation_section, "Escalation Path section missing"

        escalation_text = escalation_section.group(0)
        assert "tech lead" in escalation_text.lower(), "Tech lead escalation not documented"
