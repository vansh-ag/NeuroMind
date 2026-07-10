import requests
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

API_BASE_URL = "http://127.0.0.1:8000/api/v1"


st.set_page_config(
    page_title="NeuroMind",
    page_icon="🧠",
    layout="wide",
)


# ============================================================
# SESSION STATE
# ============================================================

if "roadmap_id" not in st.session_state:
    st.session_state.roadmap_id = None

if "roadmap" not in st.session_state:
    st.session_state.roadmap = None

if "project" not in st.session_state:
    st.session_state.project = None

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []


# ============================================================
# API HELPERS
# ============================================================

def post_request(
    endpoint: str,
    payload: dict,
    timeout: int = 120,
) -> dict:
    """
    Send a POST request to the FastAPI backend.
    """

    response = requests.post(
        f"{API_BASE_URL}{endpoint}",
        json=payload,
        timeout=timeout,
    )

    if response.status_code >= 400:
        try:
            detail = response.json().get(
                "detail",
                response.text,
            )
        except ValueError:
            detail = response.text

        raise RuntimeError(
            f"API Error ({response.status_code}): {detail}"
        )

    return response.json()


# ============================================================
# HEADER
# ============================================================

st.title("🧠 NeuroMind")

st.caption(
    "AI-powered personalized learning roadmaps, "
    "project recommendations, and roadmap-grounded tutoring."
)


# ============================================================
# SIDEBAR — ROADMAP GENERATION
# ============================================================

with st.sidebar:
    st.header("Create Learning Roadmap")

    goal_title = st.text_input(
        "Learning Goal",
        placeholder="e.g. Backend Developer",
    )

    experience = st.selectbox(
        "Experience Level",
        [
            "Less than 1 year",
            "1 to 3 years",
            "3 to 5 years",
            "More than 5 years",
        ],
    )

    known_skills_text = st.text_input(
        "Known Skills",
        placeholder="Python, SQL, Git",
    )

    learning_style = st.selectbox(
        "Learning Style",
        [
            "Project Based",
            "Theory First",
            "Balanced",
        ],
    )

    weekly_hours = st.slider(
        "Weekly Learning Hours",
        min_value=1,
        max_value=40,
        value=15,
    )

    generate_button = st.button(
        "Generate Roadmap",
        use_container_width=True,
        type="primary",
    )

    if generate_button:
        if not goal_title.strip():
            st.error(
                "Please enter a learning goal."
            )

        else:
            known_skills = [
                skill.strip()
                for skill in known_skills_text.split(",")
                if skill.strip()
            ]

            payload = {
                "goal_title": goal_title.strip(),
                "experience": experience,
                "known_skills": known_skills,
                "learning_style": learning_style,
                "weekly_hours": weekly_hours,
            }

            try:
                with st.spinner(
                    "Generating and indexing your roadmap..."
                ):
                    roadmap = post_request(
                        "/roadmaps",
                        payload,
                    )

                st.session_state.roadmap = roadmap

                st.session_state.roadmap_id = (
                    roadmap.get("roadmap_id")
                )

                st.session_state.project = None
                st.session_state.chat_messages = []

                st.success(
                    "Roadmap generated successfully."
                )

            except requests.RequestException as exc:
                st.error(
                    f"Could not connect to the backend: {exc}"
                )

            except RuntimeError as exc:
                st.error(str(exc))


# ============================================================
# CURRENT ROADMAP STATUS
# ============================================================

if st.session_state.roadmap_id:
    st.success(
        f"Active Roadmap ID: "
        f"{st.session_state.roadmap_id}"
    )
else:
    st.info(
        "Generate a roadmap from the sidebar to begin."
    )


# ============================================================
# MAIN TABS
# ============================================================

roadmap_tab, project_tab, chat_tab = st.tabs(
    [
        "🗺️ Learning Roadmap",
        "🚀 Project Recommendation",
        "💬 AI Tutor",
    ]
)


# ============================================================
# ROADMAP TAB
# ============================================================

with roadmap_tab:
    roadmap = st.session_state.roadmap

    if roadmap is None:
        st.info(
            "Generate a roadmap to view your personalized "
            "learning plan."
        )

    else:
        st.header("Your Learning Roadmap")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Estimated Hours",
                roadmap.get(
                    "estimated_hours",
                    "N/A",
                ),
            )

        with col2:
            skills = roadmap.get(
                "skills",
                [],
            )

            st.metric(
                "Skills",
                len(skills),
            )

        with col3:
            tasks = roadmap.get(
                "tasks",
                [],
            )

            st.metric(
                "Learning Tasks",
                len(tasks),
            )

        st.subheader("Recommended Skills")

        if skills:
            st.write(
                " • ".join(skills)
            )

        st.divider()

        st.subheader("Learning Path")

        for index, task in enumerate(
            tasks,
            start=1,
        ):
            task_title = task.get(
                "title",
                f"Task {index}",
            )

            estimated_hours = task.get(
                "estimated_hours",
                "N/A",
            )

            with st.expander(
                f"{index}. {task_title} "
                f"— {estimated_hours} hours",
                expanded=index == 1,
            ):
                description = task.get(
                    "description"
                )

                if description:
                    st.write(description)

                subtasks = task.get(
                    "subtasks",
                    [],
                )

                if subtasks:
                    st.markdown(
                        "**Subtasks**"
                    )

                    for subtask in subtasks:
                        title = subtask.get(
                            "title",
                            "",
                        )

                        st.markdown(
                            f"- {title}"
                        )


# ============================================================
# PROJECT TAB
# ============================================================

with project_tab:
    st.header("Project Recommendation")

    if not st.session_state.roadmap_id:
        st.info(
            "Generate a roadmap first to receive a "
            "personalized project recommendation."
        )

    else:
        st.write(
            "Generate a practical project based on your "
            "current learning roadmap."
        )

        if st.button(
            "Recommend a Project",
            type="primary",
        ):
            payload = {
                "roadmap_id": (
                    st.session_state.roadmap_id
                )
            }

            try:
                with st.spinner(
                    "Designing your project..."
                ):
                    project = post_request(
                        "/projects",
                        payload,
                    )

                st.session_state.project = project

            except requests.RequestException as exc:
                st.error(
                    f"Could not connect to the backend: {exc}"
                )

            except RuntimeError as exc:
                st.error(str(exc))

        project = st.session_state.project

        if project:
            st.subheader(
                project.get(
                    "title",
                    "Recommended Project",
                )
            )

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Difficulty",
                    project.get(
                        "difficulty",
                        "N/A",
                    ),
                )

            with col2:
                st.metric(
                    "Estimated Hours",
                    project.get(
                        "estimated_hours",
                        "N/A",
                    ),
                )

            st.subheader("Tech Stack")

            tech_stack = project.get(
                "tech_stack",
                [],
            )

            if tech_stack:
                st.write(
                    " • ".join(tech_stack)
                )

            st.subheader("Features")

            for feature in project.get(
                "features",
                [],
            ):
                st.markdown(
                    f"- {feature}"
                )

            st.subheader(
                "Why This Project?"
            )

            st.write(
                project.get(
                    "why_this_project",
                    "",
                )
            )


# ============================================================
# CHAT TAB
# ============================================================

with chat_tab:
    st.header("Ask NeuroMind")

    st.caption(
        "Answers are grounded in your generated roadmap "
        "using semantic retrieval."
    )

    if not st.session_state.roadmap_id:
        st.info(
            "Generate a roadmap first to start chatting."
        )

    else:
        for message in (
            st.session_state.chat_messages
        ):
            with st.chat_message(
                message["role"]
            ):
                st.markdown(
                    message["content"]
                )

                follow_ups = message.get(
                    "follow_ups",
                    [],
                )

                if follow_ups:
                    st.caption(
                        "Suggested follow-up questions"
                    )

                    for question in follow_ups:
                        st.markdown(
                            f"- {question}"
                        )

        user_message = st.chat_input(
            "Ask a question about your roadmap..."
        )

        if user_message:
            st.session_state.chat_messages.append(
                {
                    "role": "user",
                    "content": user_message,
                }
            )

            with st.chat_message("user"):
                st.markdown(user_message)

            payload = {
                "roadmap_id": (
                    st.session_state.roadmap_id
                ),
                "message": user_message,
            }

            try:
                with st.chat_message(
                    "assistant"
                ):
                    with st.spinner(
                        "Retrieving roadmap context..."
                    ):
                        result = post_request(
                            "/chat",
                            payload,
                        )

                    answer = result.get(
                        "response",
                        "No response received.",
                    )

                    follow_ups = result.get(
                        "follow_up_questions",
                        [],
                    )

                    st.markdown(answer)

                    if follow_ups:
                        st.caption(
                            "Suggested follow-up questions"
                        )

                        for question in follow_ups:
                            st.markdown(
                                f"- {question}"
                            )

                st.session_state.chat_messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "follow_ups": follow_ups,
                    }
                )

            except requests.RequestException as exc:
                st.error(
                    f"Could not connect to the backend: {exc}"
                )

            except RuntimeError as exc:
                st.error(str(exc))