import streamlit as st
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import re

st.set_page_config(
    page_title="GovAssist",
    page_icon="🏛️"
)

st.title("🏛️ GovAssist")
st.write("AI Government Scheme Information Assistant")


@st.cache_resource
def load_embedding_model():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )


embedding_model = load_embedding_model()


@st.cache_resource
def load_vector_store():
    return Chroma(
        collection_name="govassist",
        persist_directory="/content/govassist_db",
        embedding_function=embedding_model
    )


vector_store = load_vector_store()


question = st.text_input(
    "Ask your question",
    placeholder="Ladki Bahin Yojana ke liye kaun eligible hai?"
)


if st.button("Ask"):

    if question.strip():

        results = vector_store.similarity_search(
            question,
            k=3
        )

        if results:

            st.subheader("📌 AI Answer")

            sentences = []

            for doc in results:

                parts = re.split(
                    r'(?<=[.!?।])\s+',
                    doc.page_content
                )

                for sentence in parts:

                    sentence = sentence.strip()

                    if len(sentence) > 30:

                        sentences.append({
                            "text": sentence,
                            "page": doc.metadata.get("page", "N/A"),
                            "source": doc.metadata.get(
                                "source",
                                "Government Document"
                            )
                        })


            query_vector = embedding_model.embed_query(question)

            scored = []

            for item in sentences:

                sentence_vector = embedding_model.embed_query(
                    item["text"]
                )

                dot = sum(
                    a * b
                    for a, b in zip(
                        query_vector,
                        sentence_vector
                    )
                )

                q_norm = sum(
                    a * a
                    for a in query_vector
                ) ** 0.5

                s_norm = sum(
                    a * a
                    for a in sentence_vector
                ) ** 0.5

                score = (
                    dot / (q_norm * s_norm)
                    if q_norm and s_norm
                    else 0
                )

                item["score"] = score

                scored.append(item)


            scored.sort(
                key=lambda x: x["score"],
                reverse=True
            )


            for item in scored[:3]:

                st.write(
                    "•",
                    item["text"]
                )


            st.subheader("📚 Sources")

            shown = set()

            for item in scored[:3]:

                key = (
                    item["source"],
                    item["page"]
                )

                if key not in shown:

                    st.write(
                        f"**{item['source']}** | "
                        f"Page **{item['page']}**"
                    )

                    shown.add(key)

        else:

            st.warning(
                "Information not found in the provided government document."
            )

    else:

        st.warning(
            "Please enter a question."
        )
