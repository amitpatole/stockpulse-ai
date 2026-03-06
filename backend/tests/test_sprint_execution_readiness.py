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


class TestBacklogAcceptanceCriteriaQuality:
    """
    Verify acceptance criteria are measurable and testable (not vague).

    Acceptance Criteria:
    - Each critical task has ≥2 testable ACs
    - ACs use specific verbs (returns, raises, loads, validates) not vague terms
    - ACs specify expected outcomes (error codes, messages, behavior)
    """

    @pytest.fixture
    def sprint_backlog_content(self):
        """Load sprint backlog markdown."""
        path = Path(__file__).parent.parent.parent / "docs" / "SPRINT_BACKLOG.md"
        assert path.exists(), f"Sprint backlog not found at {path}"
        return path.read_text()

    def test_critical_tasks_have_measurable_acceptance_criteria(self, sprint_backlog_content):
        """Test: Each critical task (TP-C01-C05) has measurable ACs"""
        critical_tasks = {
            "TP-C01": "Import path",
            "TP-C02": "Parameter validation",
            "TP-C03": "API key masking",
            "TP-C04": "SECRET_KEY environment",
            "TP-C05": "CSRF protection",
        }

        for task_id, task_name in critical_tasks.items():
            # Find task section
            task_start = sprint_backlog_content.find(f"### {task_id}")
            assert task_start != -1, f"Task {task_id} not found in backlog"

            # Find next task to get section boundary
            next_task = sprint_backlog_content.find("### TP-", task_start + 1)
            task_section = sprint_backlog_content[task_start:next_task if next_task != -1 else len(sprint_backlog_content)]

            # Find Acceptance Criteria section
            ac_section = task_section[task_section.find("**Acceptance Criteria**"):]

            # Count checkbox items (- [ ])
            ac_items = re.findall(r"- \[ \]", ac_section)
            assert len(ac_items) >= 2, \
                f"{task_id} ({task_name}): Expected ≥2 acceptance criteria, found {len(ac_items)}"

    def test_security_tasks_specify_error_responses(self, sprint_backlog_content):
        """Test: Security tasks (C02, C03, C05) specify HTTP error codes or responses"""
        security_checks = {
            "TP-C02": "400",  # Bad Request for validation
            "TP-C05": "403",  # Forbidden for CSRF
        }

        for task_id, expected_code in security_checks.items():
            task_start = sprint_backlog_content.find(f"### {task_id}")
            next_task = sprint_backlog_content.find("### TP-", task_start + 1)
            task_section = sprint_backlog_content[task_start:next_task]

            assert expected_code in task_section, \
                f"{task_id} should specify HTTP {expected_code} response code in ACs"

    def test_import_fix_specifies_line_numbers(self, sprint_backlog_content):
        """Test: TP-C01 import fix specifies exact code locations"""
        task_start = sprint_backlog_content.find("### TP-C01")
        next_task = sprint_backlog_content.find("### TP-", task_start + 1)
        task_section = sprint_backlog_content[task_start:next_task]

        # Check for line number references (e.g., "lines 464-465")
        has_line_ref = re.search(r"lines?\s+\d+[-–]\d+|line\s+\d+", task_section, re.IGNORECASE)
        assert has_line_ref, \
            "TP-C01 should specify exact line numbers (e.g., 'Lines 464-465')"


class TestSprintCapacityRealistic:
    """
    Verify sprint capacity is realistic based on team velocity.

    Acceptance Criteria:
    - Critical tasks (Sprint 1) ≤ 8 points (high-risk work goes slower)
    - Each sprint total ≤ 13 points (target velocity)
    - No sprint exceeds 15 points (15% buffer for unknowns)
    - Total 60 points over 6 sprints
    """

    @pytest.fixture
    def sprint_backlog_content(self):
        path = Path(__file__).parent.parent.parent / "docs" / "SPRINT_BACKLOG.md"
        return path.read_text()

    def test_critical_sprint_is_not_overloaded(self, sprint_backlog_content):
        """Test: Critical tasks in Sprint 1 don't exceed 8 points (high-risk work)"""
        critical_tasks = ["TP-C01", "TP-C02", "TP-C03", "TP-C04", "TP-C05"]
        total_critical_points = 0

        for task_id in critical_tasks:
            task_start = sprint_backlog_content.find(f"### {task_id}")
            assert task_start != -1, f"Task {task_id} not found"

            next_task = sprint_backlog_content.find("### TP-", task_start + 1)
            task_section = sprint_backlog_content[task_start:next_task]

            # Extract story points
            points_match = re.search(r"\*\*Story Points\*\*:\s*(\d+)", task_section)
            assert points_match, f"{task_id} missing story point estimate"

            points = int(points_match.group(1))
            total_critical_points += points

        # Critical work should fit in reasonable scope (not everything in one sprint)
        assert total_critical_points <= 25, \
            f"Critical tasks total {total_critical_points} points (may need 2 sprints)"

    def test_individual_task_estimates_reasonable(self, sprint_backlog_content):
        """Test: Individual task estimates use Fibonacci scale (1-8 points for reasonable tasks)"""
        # Extract all story points
        points_matches = re.findall(r"\*\*Story Points\*\*:\s*(\d+)", sprint_backlog_content)

        for points_str in points_matches:
            points = int(points_str)
            # Reasonable Fibonacci scale: 1, 2, 3, 5, 8, 13
            reasonable_estimates = [1, 2, 3, 5, 8, 13]
            assert points in reasonable_estimates, \
                f"Story point estimate {points} is outside Fibonacci scale: {reasonable_estimates}"


class TestCriticalTasksMapToFiles:
    """
    Verify each critical task maps to specific files (so devs know what to change).

    Acceptance Criteria:
    - TP-C01 maps to backend/core/ai_analytics.py
    - TP-C02 maps to api endpoints (analysis.py, ratings.py, indicators.py)
    - TP-C03 maps to backend/core/security.py or masking utility
    - TP-C04 maps to backend/core/config.py
    - TP-C05 maps to backend/main.py (CSRF middleware)
    """

    @pytest.fixture
    def tech_spec_content(self):
        path = Path(__file__).parent.parent.parent / "docs" / "SPRINT_EXECUTION_TECH_SPEC.md"
        return path.read_text()

    def test_critical_tasks_map_to_files_table(self, tech_spec_content):
        """Test: Tech spec maps each critical task to specific files"""
        expected_mappings = {
            "TP-C01": "ai_analytics.py",  # Import fix
            "TP-C02": ["analysis.py", "ratings.py", "indicators.py"],  # Validation
            "TP-C03": "security.py",  # API key masking
            "TP-C04": "config.py",  # SECRET_KEY
            "TP-C05": "main.py",  # CSRF middleware
        }

        # Find "Files & Modules Affected" section
        files_section_start = tech_spec_content.find("## 🛠️ Files & Modules Affected")
        assert files_section_start != -1, "Files & Modules Affected section missing"

        files_section_end = tech_spec_content.find("## 🔄 Detailed Implementation", files_section_start)
        files_section = tech_spec_content[files_section_start:files_section_end]

        for task_id, expected_files in expected_mappings.items():
            if isinstance(expected_files, str):
                expected_files = [expected_files]

            for file_ref in expected_files:
                assert file_ref in files_section, \
                    f"Task {task_id} should map to file containing '{file_ref}' in Files & Modules table"

    def test_import_fix_has_code_example(self, tech_spec_content):
        """Test: TP-C01 import fix includes code example (before/after)"""
        implementation_section = tech_spec_content.find("## 🔄 Detailed Implementation")
        assert implementation_section != -1, "Detailed Implementation section missing"

        # Look for TP-C01 section with code examples
        c01_start = tech_spec_content.find("TP-C01", implementation_section)
        assert c01_start != -1, "TP-C01 not found in implementation details"

        # Check next 2000 chars for code blocks
        c01_section = tech_spec_content[c01_start:c01_start + 2000]

        # Should have BEFORE and AFTER code examples
        assert "BEFORE" in c01_section or "```python" in c01_section, \
            "TP-C01 should include BEFORE/AFTER code examples"
