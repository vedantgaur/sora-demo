"""
Prompt revision module for improving video generation based on feedback.
Automatically enhances prompts based on detected violations and quality issues.
"""
from typing import List, Dict, Any
import re

from .config import Config
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class PromptReviser:
    """Revises prompts based on agent feedback and quality metrics."""
    
    def __init__(self):
        """Initialize the prompt reviser."""
        logger.info("PromptReviser initialized")
        
        # Define revision rules based on violation types
        self.revision_rules = {
            'PhysicsViolation': [
                "with clear solid boundaries",
                "with well-defined physical structures",
                "ensuring proper collision geometry"
            ],
            'BoundaryViolation': [
                "in a contained environment",
                "with visible boundaries",
                "within a defined space"
            ],
            'ObjectPersistence': [
                "with consistent object appearance",
                "maintaining visual continuity",
                "with stable object identity"
            ],
            'DepthInconsistency': [
                "with accurate depth perception",
                "ensuring proper 3D geometry",
                "with consistent spatial relationships"
            ],
            'LowVisualQuality': [
                "in high quality",
                "with sharp details",
                "cinematic lighting"
            ],
            'MotionIssues': [
                "with smooth motion",
                "realistic movement",
                "natural animation"
            ]
        }
    
    def revise_prompt(
        self,
        original_prompt: str,
        violations: List[Dict[str, Any]],
        scores: Dict[str, float] = None
    ) -> str:
        """
        Revise a prompt based on violations and quality scores.
        
        Args:
            original_prompt: The original text prompt
            violations: List of violation dictionaries from agent testing
            scores: Optional quality scores from video scoring
        
        Returns:
            Revised prompt text
        """
        logger.info(f"Revising prompt: '{original_prompt}'")
        logger.info(f"Found {len(violations)} violations to address")
        
        revised_prompt = original_prompt.strip()
        
        # Collect all relevant improvements
        improvements = []
        
        # Add improvements based on violations
        for violation in violations:
            violation_type = violation.get('type', '')
            severity = violation.get('severity', 'medium')
            
            if violation_type in self.revision_rules:
                # Select appropriate revision based on severity
                rule = self.revision_rules[violation_type][0]
                if rule not in revised_prompt.lower():
                    improvements.append(rule)
        
        # Add improvements based on low scores
        if scores:
            if scores.get('visual_quality', 1.0) < Config.MIN_IDENTITY_PERSISTENCE:
                improvements.extend(self.revision_rules['LowVisualQuality'])
            
            if scores.get('motion_smoothness', 1.0) < Config.MIN_PATH_REALISM:
                improvements.extend(self.revision_rules['MotionIssues'])
        
        # Remove duplicates while preserving order
        improvements = list(dict.fromkeys(improvements))
        
        # Apply improvements to prompt
        if improvements:
            revised_prompt = self._apply_improvements(revised_prompt, improvements)
        
        # Additional enhancements
        revised_prompt = self._apply_general_enhancements(revised_prompt)
        
        logger.info(f"Revised prompt: '{revised_prompt}'")
        return revised_prompt
    
    def _apply_improvements(self, prompt: str, improvements: List[str]) -> str:
        """
        Apply specific improvements to the prompt.
        
        Args:
            prompt: Original prompt
            improvements: List of improvement phrases
        
        Returns:
            Prompt with improvements applied
        """
        # Check if prompt already ends with a comma or period
        prompt = prompt.rstrip()
        
        # Remove trailing punctuation if present
        if prompt.endswith(('.', ',', ';')):
            prompt = prompt[:-1]
        
        # Add improvements
        for improvement in improvements:
            if improvement.lower() not in prompt.lower():
                prompt = f"{prompt}, {improvement}"
        
        return prompt
    
    def _apply_general_enhancements(self, prompt: str) -> str:
        """
        Apply general enhancements to improve generation quality.
        
        Args:
            prompt: Prompt to enhance
        
        Returns:
            Enhanced prompt
        """
        # Add quality modifiers if not present
        quality_terms = ['high quality', 'cinematic', '4k', 'detailed']
        has_quality = any(term in prompt.lower() for term in quality_terms)
        
        if not has_quality and len(prompt.split()) < 30:  # Don't add if prompt is already long
            prompt = f"{prompt}, cinematic shot"
        
        # Ensure proper capitalization
        if prompt and not prompt[0].isupper():
            prompt = prompt[0].upper() + prompt[1:]
        
        return prompt
    
    def suggest_alternative_prompts(
        self,
        original_prompt: str,
        num_alternatives: int = 3
    ) -> List[str]:
        """
        Generate alternative prompt variations.
        
        Args:
            original_prompt: The original prompt
            num_alternatives: Number of alternatives to generate
        
        Returns:
            List of alternative prompts
        """
        alternatives = []
        
        # Alternative 1: Add camera angle
        alt1 = f"{original_prompt}, wide angle shot"
        alternatives.append(alt1)
        
        # Alternative 2: Add lighting
        alt2 = f"{original_prompt}, well-lit scene with soft lighting"
        alternatives.append(alt2)
        
        # Alternative 3: Add environmental details
        alt3 = f"{original_prompt}, detailed environment with clear spatial layout"
        alternatives.append(alt3)
        
        # Alternative 4: Add motion description
        alt4 = f"{original_prompt}, smooth and realistic motion"
        alternatives.append(alt4)
        
        return alternatives[:num_alternatives]
    
    def analyze_prompt_quality(self, prompt: str) -> Dict[str, Any]:
        """
        Analyze the quality and completeness of a prompt.
        
        Args:
            prompt: Prompt to analyze
        
        Returns:
            Dictionary with quality metrics and suggestions
        """
        analysis = {
            'length': len(prompt.split()),
            'has_subject': bool(self._extract_subject(prompt)),
            'has_action': bool(self._extract_action(prompt)),
            'has_environment': bool(self._extract_environment(prompt)),
            'has_style': bool(self._extract_style(prompt)),
            'has_quality_terms': any(
                term in prompt.lower()
                for term in ['high quality', 'detailed', 'cinematic', '4k', '8k']
            ),
            'suggestions': []
        }
        
        # Generate suggestions
        if not analysis['has_subject']:
            analysis['suggestions'].append("Consider adding a clear subject (person, object, character)")
        
        if not analysis['has_action']:
            analysis['suggestions'].append("Consider adding an action or movement")
        
        if not analysis['has_environment']:
            analysis['suggestions'].append("Consider describing the environment or setting")
        
        if not analysis['has_style']:
            analysis['suggestions'].append("Consider adding style descriptors (cinematic, artistic, etc.)")
        
        if analysis['length'] < 5:
            analysis['suggestions'].append("Prompt is quite short; consider adding more details")
        
        return analysis
    
    def _extract_subject(self, prompt: str) -> str:
        """Extract the main subject from a prompt."""
        # Simple heuristic: look for nouns at the start
        words = prompt.split()
        if len(words) > 0:
            return words[0]
        return ""
    
    def _extract_action(self, prompt: str) -> str:
        """Extract action verbs from a prompt."""
        action_verbs = [
            'walk', 'run', 'jump', 'fly', 'swim', 'drive', 'move', 'spin',
            'rotate', 'explor', 'travel', 'float', 'dance', 'fight'
        ]
        prompt_lower = prompt.lower()
        for verb in action_verbs:
            if verb in prompt_lower:
                return verb
        return ""
    
    def _extract_environment(self, prompt: str) -> str:
        """Extract environment descriptors from a prompt."""
        env_terms = [
            'hallway', 'room', 'street', 'forest', 'beach', 'city', 'space',
            'indoor', 'outdoor', 'building', 'landscape', 'scene', 'environment'
        ]
        prompt_lower = prompt.lower()
        for term in env_terms:
            if term in prompt_lower:
                return term
        return ""
    
    def _extract_style(self, prompt: str) -> str:
        """Extract style descriptors from a prompt."""
        style_terms = [
            'cinematic', 'artistic', 'realistic', 'cartoon', 'anime', 'photorealistic',
            'stylized', 'abstract', 'dramatic', 'beautiful', 'stunning'
        ]
        prompt_lower = prompt.lower()
        for term in style_terms:
            if term in prompt_lower:
                return term
        return ""
    
    def create_revision_explanation(
        self,
        original_prompt: str,
        revised_prompt: str,
        violations: List[Dict[str, Any]]
    ) -> str:
        """
        Create a human-readable explanation of why the prompt was revised.
        
        Args:
            original_prompt: Original prompt
            revised_prompt: Revised prompt
            violations: List of violations that triggered revision
        
        Returns:
            Explanation text
        """
        if not violations:
            return "No major issues detected. Prompt slightly enhanced for quality."
        
        violation_types = [v.get('type', 'Unknown') for v in violations]
        unique_types = list(dict.fromkeys(violation_types))
        
        explanation = f"Revised prompt to address {len(violations)} issue(s):\n"
        
        for vtype in unique_types:
            count = violation_types.count(vtype)
            explanation += f"- {vtype}: {count} occurrence(s)\n"
        
        explanation += f"\nOriginal: {original_prompt}\n"
        explanation += f"Revised: {revised_prompt}"
        
        return explanation


# Singleton instance
_prompt_reviser = None

def get_prompt_reviser() -> PromptReviser:
    """Get the singleton PromptReviser instance."""
    global _prompt_reviser
    if _prompt_reviser is None:
        _prompt_reviser = PromptReviser()
    return _prompt_reviser


def revise_prompt(
    original_prompt: str,
    violations: List[Dict[str, Any]],
    scores: Dict[str, float] = None
) -> str:
    """Convenience function to revise a prompt."""
    reviser = get_prompt_reviser()
    return reviser.revise_prompt(original_prompt, violations, scores)

