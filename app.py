
import streamlit as st
import google.generativeai as genai
import os

# --- Application Page Settings ---
# This MUST be the first Streamlit command in your script.
st.set_page_config(page_title="LLM2LLL Customizable Mentor", page_icon=None) # Emojis removed

# --- Default System Prompt ---
DEFAULT_SYSTEM_PROMPT = "You are an experienced mentor for occupational therapists. You must provide professional, supportive and Short answers. Use clear and respectful language."

# --- Model Loading Function (cached based on system_instruction) ---
@st.cache_resource
def get_generative_model(system_instruction_payload):
    st.sidebar.write(f"Loading/Re-initializing model with new system prompt...") # Visual feedback
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=system_instruction_payload
        )
        return model
    except Exception as e:
        st.error(f"Error creating GenerativeModel with the provided system prompt: {e}")
        return None

# --- API Key Configuration ---
ACTUAL_API_KEY = os.environ.get("GOOGLE_API_KEY_FOR_APP")

if not ACTUAL_API_KEY:
    st.error("Critical error: Google API key is missing. Configure it in the deployment platform's secrets management.")
    st.caption("This application cannot function without a valid Google API Key.")
    st.stop() 

try:
    genai.configure(api_key=ACTUAL_API_KEY)
except Exception as e:
    st.error(f"Error configuring the Google GenAI API: {e}")
    st.stop()

# --- Sidebar for System Prompt Configuration ---
st.sidebar.header("Mentor Configuration") # Emoji removed
custom_system_prompt = st.sidebar.text_area(
    "Define the mentor's behavior (System Prompt):",
    value=st.session_state.get("system_prompt_for_chat", DEFAULT_SYSTEM_PROMPT), 
    height=250,
    key="system_prompt_input_widget"
)

if "system_prompt_for_chat" not in st.session_state:
    st.session_state.system_prompt_for_chat = DEFAULT_SYSTEM_PROMPT

if st.sidebar.button("Apply New System Prompt & Restart Chat"):
    if custom_system_prompt != st.session_state.system_prompt_for_chat:
        st.session_state.system_prompt_for_chat = custom_system_prompt
        st.session_state.messages = []
        if "chat_session" in st.session_state:
            del st.session_state.chat_session 
        st.sidebar.success("System prompt updated! Chat has been reset.")
        st.experimental_rerun() 
    else:
        st.sidebar.info("System prompt is the same as the current one. No changes applied.")

# --- Load Model ---
model = get_generative_model(st.session_state.system_prompt_for_chat)

if not model:
    st.error("Failed to load the generative model. Application cannot proceed.")
    st.stop()

# --- Chat Session Initialization ---
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])
    if not st.session_state.get("messages"): 
         st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I assist you today based on the current system prompt?"}]

if "messages" not in st.session_state: 
    st.session_state.messages = []

# --- Main Application UI ---
st.title("LLM2LLL") 
st.markdown("Welcome! This chat provides mentoring, guidance, and advice for occupational therapists. You can customize the mentor's behavior using the sidebar.") 
st.caption("Powered by Gemini 1.5 Flash")

# --- Displaying Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]): # Avatars removed, Streamlit will use defaults
        st.markdown(message["content"])

# --- Getting User Input and Processing It ---
if user_prompt := st.chat_input("Type your question here..."):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"): # Avatars removed
        st.markdown(user_prompt)

    if "chat_session" in st.session_state: 
        try:
            chat_session_to_use = st.session_state.chat_session
            model_response = chat_session_to_use.send_message(user_prompt)
            response_text = model_response.text

            st.session_state.messages.append({"role": "assistant", "content": response_text})
            with st.chat_message("assistant"): # Avatars removed
                st.markdown(response_text)

        except Exception as e:
            error_for_display = f"Oops, an error occurred while communicating with the model: {e}"
            st.session_state.messages.append({"role": "assistant", "content": error_for_display})
            with st.chat_message("assistant"): # Avatars removed
                st.error(error_for_display)
            st.toast(f"Error: {e}") # Emoji removed from toast by default (no icon specified)
    else:
        st.error("Chat session is not initialized. Please ensure the model and system prompt are correctly configured.")
