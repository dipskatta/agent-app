import streamlit as st
import pandas as pd
import os
import io
import re
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

# Load OpenAI API key
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(temperature=0)

st.set_page_config(page_title="Platform Strategic Capabilities Assistant")
st.title("📊 Platform Strategic Capabilities Assistant")

# Upload Excel files
platform_file = st.file_uploader("📂 Upload Excel with Platforms (must have 'Platform' column)", type=["xlsx"])
requirement_file = st.file_uploader("📌 Upload Excel with Requirements (must have 'Requirement' column)", type=["xlsx"])

# Prompts
prompt_1 = st.text_input("💬 Prompt 1 (Ask a question about platforms)", "What platforms does this client have?")
prompt_2 = st.text_input("💬 Prompt 2 (Summarize each platform)", "Give me a summary of each platform")
prompt_3 = st.text_input("💬 Prompt 3 (Strategic analysis)", "What additional platforms would I need based on requirements?")

# Helper function to load Excel column
def load_column(file, col_name) -> list:
    df = pd.read_excel(file)
    if col_name not in df.columns:
        return None
    return df[col_name].dropna().tolist()

if platform_file and requirement_file:
    platforms = load_column(platform_file, "Platform")
    requirements = load_column(requirement_file, "Requirement")

    if not platforms:
        st.error("⚠️ 'Platform' column not found in platform file.")
    elif not requirements:
        st.error("⚠️ 'Requirement' column not found in requirement file.")
    else:
        platforms_text = ", ".join(platforms)

        # Prompt 1
        if prompt_1:
            st.subheader("📋 Client Platforms")
            messages = [
                SystemMessage(content="You are a helpful assistant that answers questions about a list of client platforms."),
                HumanMessage(content=f"The platforms are: {platforms_text}"),
                HumanMessage(content=prompt_1)
            ]
            response1 = llm(messages)
            st.success("Response to Prompt 1:")
            st.write(response1.content)

        # Prompt 2 - Summaries
        st.subheader("🧠 Platform Summaries")
        summaries = []
        with st.spinner("Fetching summaries..."):
            for platform in platforms:
                query = f"{prompt_2}: {platform}"
                messages = [
                    SystemMessage(content="You are a marketing analyst who provides brief summaries of digital platforms."),
                    HumanMessage(content=query)
                ]
                response = llm(messages)
                summaries.append((platform, response.content))

        for plat, summary in summaries:
            st.markdown(f"**{plat}**: {summary}")

        # Requirement Mapping
        st.subheader("📌 Requirement Mapping & Recommendations")
        summary_text = "\n".join([f"{p}: {s}" for p, s in summaries])
        requirements_text = ", ".join(requirements)
        mapping_prompt = f"""
Given the following platform summaries:

{summary_text}

And the business requirements: {requirements_text}

1. Map which platforms meet which requirements.
2. List any platforms that do not align with the stated requirements.
3. Suggest additional platforms (new platforms that are not in the list above) that might fulfill these business needs. 
Provide these new platform suggestions in a list format:
Suggested additional platforms: [comma-separated list]
"""
        messages = [
            SystemMessage(content="You are a strategic marketing assistant helping match platforms to business needs."),
            HumanMessage(content=mapping_prompt)
        ]
        with st.spinner("Analyzing requirements..."):
            response3 = llm(messages)
        st.success("Requirements Analysis:")
        st.write(response3.content)

        # Extract new platform suggestions
        suggested_clean = []
        suggestion_match = re.findall(r"Suggested additional platforms: (.*)", response3.content)
        if suggestion_match:
            suggested_clean = [s.strip() for s in suggestion_match[0].split(",") if s.strip() and s.strip() not in platforms]

        st.subheader("➕ Add Platforms to List")

        selected = []
        if suggested_clean:
            selected = st.multiselect("✅ Select suggested platforms to add:", suggested_clean)
        else:
            st.info("ℹ️ No clean platform suggestions found. You can still manually enter a platform.")

        manual_platform = st.text_input("📝 Or enter a platform manually to add:")
        if manual_platform:
            selected.append(manual_platform.strip())

        # Update Excel
        if selected:
            updated_platforms = platforms + [p for p in selected if p not in platforms]
            updated_df = pd.DataFrame({"Platform": updated_platforms})
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                updated_df.to_excel(writer, index=False, sheet_name="Platforms")
            buffer.seek(0)

            st.success("✅ Platforms added. Download the updated list below:")
            st.download_button(
                label="📥 Download Updated Excel",
                data=buffer,
                file_name="updated_platforms.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # Prompt 3 - Strategic insight
        if prompt_3:
            st.subheader("🧩 Strategic Insight")
            custom_prompt = f"""
Given the following platform summaries:

{summary_text}

And the business requirements: {requirements_text}

Now answer the following user question:
{prompt_3}
"""
            messages = [
                SystemMessage(content="You are a strategic advisor helping map platforms to business needs."),
                HumanMessage(content=custom_prompt)
            ]
            with st.spinner("Thinking..."):
                response4 = llm(messages)
            st.success("Insight:")
            st.write(response4.content)
