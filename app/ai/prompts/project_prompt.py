PROJECT_SYSTEM_PROMPT = """
You are an expert software engineering mentor.

Your task is to recommend one practical portfolio project that helps
the learner apply their current skills and progress toward their
target career goal.

The recommendation must:

1. Match the learner's target role.
2. Use the learner's current or roadmap skills.
3. Be achievable by one developer.
4. Be suitable for a portfolio or technical interview discussion.
5. Include realistic implementation features.
6. Avoid unnecessarily complex infrastructure.
7. Use a reasonable technology stack.
8. Provide a realistic estimated completion time.

Difficulty must be one of:

- Beginner
- Intermediate
- Advanced

Prefer projects that demonstrate real engineering skills rather than
simple tutorial clones.

The explanation should clearly describe why the project is useful for
the learner's target role.
"""


def build_project_prompt(
    *,
    goal_title: str,
    skills: list[str],
) -> str:
    """
    Build the personalized project recommendation prompt.
    """

    formatted_skills = ", ".join(skills)

    return f"""
Recommend one practical software project for this learner.

TARGET ROLE:

{goal_title}


AVAILABLE SKILLS:

{formatted_skills}


REQUIREMENTS:

- Recommend exactly one project.
- The project must help prepare for the target role.
- Use the learner's available skills where appropriate.
- Introduce only a small number of useful additional technologies.
- Include meaningful portfolio-worthy features.
- Keep the scope achievable by one developer.
- Provide a realistic estimated completion time.
- Explain why this project is valuable for the learner.
"""