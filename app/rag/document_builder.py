from dataclasses import dataclass

from app.models.roadmap import Roadmap


@dataclass
class RoadmapDocument:
    """
    Semantic document created from one roadmap task.
    """

    chunk_index: int
    task_title: str
    content: str


def build_roadmap_documents(
    roadmap: Roadmap,
) -> list[RoadmapDocument]:
    """
    Convert a roadmap into semantic task-level documents.

    Chunking strategy:
    - one roadmap task becomes one chunk;
    - each chunk includes roadmap-level context;
    - subtasks stay with their parent task;
    - task order is preserved.

    This is more suitable than arbitrary character-based
    chunking because the roadmap already has semantic boundaries.
    """

    documents: list[RoadmapDocument] = []

    for task in roadmap.tasks:
        subtasks_text = "\n".join(
            f"- {subtask.title}"
            for subtask in task.subtasks
        )

        content = f"""
Learning Goal: {roadmap.goal_title}
Experience Level: {roadmap.experience}
Learning Style: {roadmap.learning_style}
Weekly Learning Hours: {roadmap.weekly_hours}

Task Order: {task.sequence_order}
Task Title: {task.title}

Task Description:
{task.description}

Estimated Task Hours:
{task.estimated_hours}

Subtasks:
{subtasks_text}
""".strip()

        documents.append(
            RoadmapDocument(
                chunk_index=task.sequence_order,
                task_title=task.title,
                content=content,
            )
        )

    return documents