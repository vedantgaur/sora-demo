"""Tests for the Prompt Reviser module."""
import pytest

from src.prompt_reviser import PromptReviser, revise_prompt


@pytest.fixture
def prompt_reviser():
    """Create a PromptReviser instance."""
    return PromptReviser()


def test_revise_prompt_with_physics_violation(prompt_reviser):
    """Test prompt revision with physics violations."""
    original = "A robot walks down a hallway"
    violations = [
        {
            'type': 'PhysicsViolation',
            'description': 'Collision detected',
            'severity': 'high'
        }
    ]
    
    revised = prompt_reviser.revise_prompt(original, violations)
    
    assert revised != original
    assert "boundaries" in revised.lower() or "physical" in revised.lower()


def test_revise_prompt_with_multiple_violations(prompt_reviser):
    """Test revision with multiple violation types."""
    original = "A robot walks"
    violations = [
        {'type': 'PhysicsViolation', 'severity': 'high'},
        {'type': 'BoundaryViolation', 'severity': 'medium'},
    ]
    
    revised = prompt_reviser.revise_prompt(original, violations)
    
    assert len(revised) > len(original)


def test_revise_prompt_with_no_violations(prompt_reviser):
    """Test that revision with no violations still enhances."""
    original = "A simple scene"
    violations = []
    
    revised = prompt_reviser.revise_prompt(original, violations)
    
    # Should add quality enhancements even with no violations
    assert len(revised) >= len(original)


def test_analyze_prompt_quality(prompt_reviser):
    """Test prompt quality analysis."""
    prompt = "A robot walks down a futuristic hallway"
    
    analysis = prompt_reviser.analyze_prompt_quality(prompt)
    
    assert 'length' in analysis
    assert 'has_subject' in analysis
    assert 'has_action' in analysis
    assert 'suggestions' in analysis
    assert analysis['has_subject'] is True
    assert analysis['has_action'] is True


def test_analyze_incomplete_prompt(prompt_reviser):
    """Test analysis of an incomplete prompt."""
    prompt = "Something"
    
    analysis = prompt_reviser.analyze_prompt_quality(prompt)
    
    assert len(analysis['suggestions']) > 0


def test_suggest_alternative_prompts(prompt_reviser):
    """Test alternative prompt generation."""
    original = "A robot walks"
    
    alternatives = prompt_reviser.suggest_alternative_prompts(original, num_alternatives=3)
    
    assert len(alternatives) == 3
    for alt in alternatives:
        assert len(alt) > len(original)


def test_create_revision_explanation(prompt_reviser):
    """Test revision explanation generation."""
    original = "A robot walks"
    revised = "A robot walks, with clear solid boundaries"
    violations = [{'type': 'PhysicsViolation', 'severity': 'high'}]
    
    explanation = prompt_reviser.create_revision_explanation(
        original, revised, violations
    )
    
    assert original in explanation
    assert revised in explanation
    assert 'PhysicsViolation' in explanation


def test_convenience_function():
    """Test the convenience revise_prompt function."""
    violations = [{'type': 'PhysicsViolation', 'severity': 'high'}]
    revised = revise_prompt("A scene", violations)
    
    assert isinstance(revised, str)
    assert len(revised) > 0

