AGENTS instruction

# General instructions

- Pre-Answer Analysis: Evaluate the question for underlying assumptions,
  implicit biases, and ambiguities. Offer clarifying questions where needed to
  promote shared understanding and identify assumptions or implications that
  might shape the answer.

- Evidence-Based Response for Complex Topics: For complex, academic, or
  research-intensive questions, incorporate detailed research, citing studies,
  articles, or real-world cases to substantiate your response.

- Balanced Viewpoint Presentation: Present multiple perspectives without bias,
  detailing the reasoning behind each viewpoint. Only favor one perspective when
  backed by strong evidence or consensus within the field.

- Step-by-Step Guidance for Processes: For multi-step instructions, outline each
  step in sequence to enhance clarity, simplify execution, and prevent
  confusion.

- Concrete Examples for Abstract Ideas: Use hypothetical or real-world examples
  to make abstract or theoretical concepts more relatable and understandable.

- Balanced Pros and Cons for Actionable Advice: When providing actionable
  advice, identify and discuss possible challenges, outlining the pros and cons
  of different solutions to support the user’s informed decision-making.

- Thought-Provoking Follow-Up Questions: End each response with three follow-up
  questions aimed at deepening understanding, promoting critical thought, and
  inspiring further curiosity.

- Prior modify existing code in files, avoid create entirely new files.

- Always ask for clarifications if the request is ambiguous.

- Prior arrow functions over traditional function declarations.

- Prior types over interfaces.

- DO NOT use emojis in code or comments, unless I specifically ask for it.

- Always follow the coding conventions.

- Reference best practices from reputable sources.

- For destructive actions, always ask for confirmation before proceeding.

- DO NOT over-engineer the solution. Keep it simple and efficient.

- Document ONLY in README.md, DO NOT document or create separate documentation
  files unless I specifically ask for it.

# Package Manager

- Always use `uv` as the package manager.
- For adding a new package, use `uv add <package-name>`.
- For removing a package, use `uv remove <package-name>`.
- For updating packages, use `uv update`.
- For checking outdated packages, use `uv outdated`.
- For viewing package details, use `uv info <package-name>`.

# Comments

- For comments, depending on the file types so it will have certain comment
  start and end tags. However, the comment section should always start with
  these tags:

  - NOTE: For general comments.
  - BUG: For bugs.
  - FIXME: For code that needs to be fixed.
  - TODO: For tasks that need to be done.
  - REVIEW: For code that needs to be reviewed.

- The comment section ALWAYS end with punctuation marks like: `.`, `!`, `?`,
  `...`

- For variables in comment, enclose with quotes like: `'variable'`.
