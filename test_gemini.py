import asyncio

from app.ai.client import gemini_client
from app.schemas.roadmap import RoadmapRequest


async def main():
    request = RoadmapRequest(
        goal_title="Backend Developer",
        experience="Less than 1 year",
        known_skills=[
            "Python",
            "SQL",
        ],
        learning_style="Project Based",
        weekly_hours=15,
    )

    roadmap = await gemini_client.generate_roadmap(
        request
    )

    print(
        roadmap.model_dump_json(
            indent=2
        )
    )


if __name__ == "__main__":
    asyncio.run(main())