# Style Guide for Gemini Code Assistant (Timesketch-Inspired)

This style guide outlines the coding and documentation standards for the Gemini Code Assistant, drawing inspiration from the Timesketch project's practices and adapting them for the unique context of an AI coding assistant.

## I. Code Style

### A. General Principles

1.  **Readability:** Code should be clear, concise, and easy to understand. Favor clarity over cleverness.
2.  **Consistency:** Maintain a consistent style throughout the codebase.
3.  **Maintainability:** Write code that is easy to modify and extend.
4.  **Efficiency:** Strive for efficient algorithms and data structures, but don't sacrifice readability for minor performance gains.
5.  **Testability:** Design code that is easy to test.

### B. Language-Specific Guidelines

1.  **Python:**
    *   **Adherence to PEP 8:** Follow the official Python style guide (PEP 8) for formatting, naming conventions, and code layout.
    *   **Docstrings:** Use docstrings to explain the purpose, parameters, and return values of functions, classes, and modules.
    *   **Docstring Format:** Use [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
    *   **Type Hints:** Employ type hints to improve code clarity and enable static analysis.
    *   **Error Handling:** Use exceptions for error handling and provide informative error messages. When catching exceptions, use `as e:` (e.g., `except ValueError as e:`).
    *   **String Formatting:** Prefer f-strings for all string formatting (e.g., `f"User: {username}"`). The only exception is for logging messages, which should use the older `%` style to allow for deferred formatting, as enforced by the linter configuration.
    *   **Imports:** Organize imports into standard library, third-party, and local modules, separated by blank lines.
    *   **Comments:** Use comments to explain non-obvious code or complex logic.
    *   **Tooling:** Use **Pylint** for linting and **Black** for code formatting. Configurations are in `.pylintrc` and `pyproject.toml` respectively.
    *   **Quotes:** Use double quotes (`"`) for strings. `black` will enforce this automatically. Use triple double quotes (`"""`) for docstrings and multi-line strings.
    *   **Pylint Overrides:** Use textual pylint overrides (e.g., `# pylint: disable=no-self-argument`) instead of numeric codes (`# pylint: disable=E0213`).

2.  **JavaScript/TypeScript:**
    *   **ESLint:** Use ESLint to enforce code quality and style.
    *   **Naming Conventions:** Use camelCase for variables and functions, PascalCase for classes and components.
    *   **Comments:** Use comments to explain non-obvious code or complex logic.
    *   **Formatting:** Use consistent indentation and spacing.
    *   **Error Handling:** Use try-catch blocks for error handling.
    *   **Asynchronous Code:** Use async/await for asynchronous operations.
    *   **Semicolons:** Use semicolons at the end of statements, as enforced by the project's linter.

3.  **Other Languages:**
    *   Follow the established style guides and best practices for each language.
    *   Maintain consistency within each language's codebase.

### C. Naming Conventions

1.  **Descriptive Names:** Use descriptive names for variables, functions, classes, and modules.
2.  **Consistency:** Be consistent in your naming conventions.
3.  **Avoid Abbreviations:** Avoid overly short or cryptic abbreviations.
4.  **Meaningful Names:** Names should convey the purpose or meaning of the entity they represent.

## II. Documentation Style

This section covers documentation within the code, for users, and for contributors.

### A. Commit Message Style

Commit messages should follow the Conventional Commits specification. This creates an explicit commit history, which makes it easier to track features, fixes, and breaking changes.

The basic format is:
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```
*   **Types:** `feat`, `fix`, `build`, `chore`, `ci`, `docs`, `style`, `refactor`, `perf`, `test`.
*   **Scope:** A noun describing a section of the codebase (e.g., `api`, `tsctl`, `frontend`).

### B. General Principles

1.  **Clarity:** Documentation should be clear, concise, and easy to understand.
2.  **Accuracy:** Documentation should be accurate and up-to-date.
3.  **Completeness:** Documentation should be complete and cover all relevant aspects of the code.
4.  **Consistency:** Maintain a consistent style throughout the documentation.
5.  **Audience:** Consider the intended audience when writing documentation.

### C. Documentation Types

1.  **Code Comments:**
    *   Explain non-obvious code or complex logic.
    *   Keep comments concise and relevant.
    *   Update comments when the code changes.

2.  **Docstrings:**
    *   Use docstrings to explain the purpose, parameters, and return values of functions, classes, and modules.
    *   Follow the language-specific conventions for docstring formatting.

3.  **README Files:**
    *   Provide an overview of the project.
    *   Explain how to set up and use the project.
    *   Include examples and usage scenarios.
    *   Link to other relevant documentation.

4.  **API Documentation:**
    *   Document all public APIs.
    *   Explain the purpose, parameters, and return values of each API.
    *   Provide examples of how to use the API.

5.  **Tutorials and Guides:**
    *   Create tutorials and guides for common tasks or use cases.
    *   Provide step-by-step instructions.
    *   Include examples and code snippets.

### D. Markdown Formatting

1.  **Headings:** Use headings to organize the documentation.
2.  **Lists:** Use lists to present items in a clear and concise way.
3.  **Code Blocks:** Use code blocks to display code snippets.
4.  **Emphasis:** Use bold and italic text for emphasis.
5.  **Links:** Use links to refer to other documentation or resources.

## III. Contribution Guidelines

### A. Code Review

1.  **All submissions, including submissions by project members, require review.**
2.  **Code should be easy to maintain and understand.**
3.  **Quick-and-dirty solutions are discouraged.**
4.  **At least two reviewers should look over the code.**
5.  **Auto generated UI builds may be merged without review by core project members.**

### B. Documentation Review

1.  **Simple documentation updates and additions made by core project members may be merged without review.**
2.  **Any change that affects the layout and structure of the site has to go through the review process.**
3.  **Any update from external contributors has to be reviewed.**

### C. Pull Requests

1.  **Fork the repository.**
2.  **Create a new branch for your changes.**
3.  **Make your changes and commit them.**
4.  **Push your changes to your fork.**
5.  **Create a pull request.**
 6.  **Run linters locally (`black`, `pylint`, `eslint`) before submitting to catch style issues early.**
6.  **Address any feedback from the reviewers.**

### D. Testing

1.  **Write unit tests for your code.**
2.  **Ensure that all tests pass before submitting a pull request.**
3.  **Add new tests for new features or bug fixes.**

## IV. Additional Considerations for a Code Assistant

### A. Code Generation

1.  **Context Awareness:** The code assistant should be aware of the context in which it is generating code.
2.  **Code Completeness:** Generated code should be complete and functional.
3.  **Code Correctness:** Generated code should be correct and free of errors.
4.  **Code Style:** Generated code should adhere to the style guide.
5.  **Code Efficiency:** Generated code should be efficient.
6.  **Code Security:** Generated code should be secure.
7.  **Code Testability:** Generated code should be testable.

### B. Code Understanding

1.  **Code Analysis:** The code assistant should be able to analyze code and understand its structure and behavior.
2.  **Code Refactoring:** The code assistant should be able to refactor code to improve its quality.
3.  **Code Debugging:** The code assistant should be able to help debug code.
4.  **Code Explanation:** The code assistant should be able to explain code to users.

### C. User Interaction

1.  **Clear Prompts:** The code assistant should provide clear prompts to users.
2.  **Helpful Responses:** The code assistant should provide helpful responses to user queries.
3.  **Error Handling:** The code assistant should handle errors gracefully.
4.  **User Feedback:** The code assistant should be able to learn from user feedback.

## V. License

All code and documentation are licensed under the Apache License, Version 2.0.
