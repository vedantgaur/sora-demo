# Contributing to Sora Director

Thank you for your interest in contributing to the Sora Director project! This document provides guidelines and instructions for contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/sora-demo.git
   cd sora-demo
   ```
3. **Create a new branch** for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

1. **Install dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

2. **Set up pre-commit hooks** (optional but recommended):
   ```bash
   pre-commit install
   ```

3. **Run the application** in development mode:
   ```bash
   python src/main.py
   ```

## Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all functions, classes, and modules
- Keep functions focused and concise
- Use meaningful variable and function names

### Formatting

Run these commands before committing:

```bash
# Format code
black src/

# Sort imports
isort src/

# Check for issues
flake8 src/
mypy src/
```

## Testing

1. **Write tests** for new features in the `tests/` directory
2. **Run tests** before submitting:
   ```bash
   pytest
   pytest --cov=src tests/  # With coverage
   ```
3. Ensure all tests pass and maintain or improve code coverage

## Making Changes

1. **Keep commits focused**: Each commit should represent a single logical change
2. **Write clear commit messages**:
   ```
   Short (50 chars or less) summary
   
   More detailed explanatory text, if necessary. Wrap at 72 characters.
   Explain the problem that this commit is solving. Focus on why you
   are making this change as opposed to how.
   ```

3. **Update documentation**: If your changes affect usage, update the README or relevant docs

## Submitting Changes

1. **Push your changes** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** on GitHub with:
   - A clear title and description
   - Reference to any related issues
   - Screenshots/demos if applicable
   - Test results

3. **Respond to feedback**: Be prepared to make changes based on code review

## Areas for Contribution

### High Priority
- Real Sora API integration
- Advanced 3D reconstruction pipeline
- VLA agent implementation
- Performance optimization

### Feature Enhancements
- Additional video quality metrics
- Multiple 3D asset formats
- Advanced prompt revision strategies
- Audio-visual sync testing

### Infrastructure
- Async task processing (Celery)
- Database integration (PostgreSQL)
- Caching layer (Redis)
- CI/CD pipeline improvements

### Documentation
- API documentation
- Architecture diagrams
- Tutorial videos
- Example prompts and results

## Reporting Bugs

When reporting bugs, please include:
- **Description**: Clear description of the issue
- **Steps to reproduce**: Detailed steps to reproduce the bug
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Environment**: OS, Python version, relevant dependencies
- **Logs**: Any relevant error messages or logs

## Feature Requests

For feature requests:
- **Describe the feature**: Clear description of what you want
- **Use case**: Explain why this feature would be useful
- **Alternatives**: Have you considered any alternative solutions?
- **Implementation ideas**: Any thoughts on how it could be implemented?

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone.

### Our Standards

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards others

### Enforcement

Unacceptable behavior may be reported to the project maintainers. All complaints will be reviewed and investigated.

## Questions?

If you have questions about contributing:
- Open an issue with the "question" label
- Check existing issues and documentation
- Reach out to the maintainers

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

Thank you for contributing to Sora Director! 🎬

