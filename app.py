
import streamlit as st
import google.generativeai as genai
import os

# --- Application Page Settings ---
# This MUST be the first Streamlit command in your script.
st.set_page_config(page_title="LLM2LLL Customizable Mentor", page_icon=None)

# --- Default System Prompt ---
DEFAULT_SYSTEM_PROMPT = "You are an experienced mentor for occupational therapists. You must provide professional, supportive and Short answers. Use clear and respectful language."

# --- Model Loading Function (cached based on system_instruction) ---
@st.cache_resource
def get_generative_model(system_instruction_payload):
    # This function is designed to be called after API key is configured.
    # We add a print to sidebar here just to confirm if this part of code is ever reached.
    # st.sidebar.write(f"Attempting to load model with prompt: {system_instruction_payload[:30]}...") # Debug
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=system_instruction_payload
        )
        return model
    except Exception as e:
        # This error will appear in the main panel if model loading fails
        st.error(f"Error creating GenerativeModel: {e}")
        return None

# --- API Key Configuration ---
# This is a critical step. If it fails, the script might stop before rendering the sidebar.
st.text("DEBUG: Checking API Key...") # Temporary debug message

ACTUAL_API_KEY = os.environ.get("GOOGLE_API_KEY_FOR_APP")

if not ACTUAL_API_KEY:
    st.error("CRITICAL ERROR: Google API key (GOOGLE_API_KEY_FOR_APP) is missing from environment secrets.")
    st.caption("Please ensure you have correctly set this secret in your deployment platform (e.g., Streamlit Community Cloud settings). The application cannot proceed without it.")
    st.stop() # Halts script execution if key is missing

try:
    genai.configure(api_key=ACTUAL_API_KEY)
    st.text("DEBUG: genai.configure(api_key=...) successful.") # Temporary debug message
except Exception as e:
    st.error(f"CRITICAL ERROR: Error configuring the Google GenAI API with the provided key: {e}")
    st.caption("This might indicate an invalid API key or a problem with the Google Cloud project.")
    st.stop() # Halts script execution if configuration fails

# --- Sidebar for System Prompt Configuration ---
# If the script reaches this point, the API key was found and genai.configure was successful.
st.sidebar.info("Sidebar rendering started.") # Debug message IN THE SIDEBAR
st.sidebar.header("Mentor Configuration")
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
        st.session_state.messages = [] # Clear chat history
        if "chat_session" in st.session_state:
            del st.session_state.chat_session # Delete old chat session
        
        # Clear the cached model to ensure the new system prompt is used for model re-creation
        # Note: get_generative_model is keyed by its argument, so calling it with a new
        # system_prompt_for_chat should inherently lead to a new/different cached model instance.
        # Explicitly clearing might be an option if issues persist:
        # get_generative_model.clear() # Uncomment this if you suspect caching issues with system prompt changes

        st.sidebar.success("System prompt updated! Chat has been reset.")
        st.experimental_rerun() # Rerun the script to apply all changes cleanly
    else:
        st.sidebar.info("System prompt is the same as the current one. No changes applied.")

st.sidebar.markdown("---") # Separator in sidebar

# --- Load Model (uses the system prompt from session state) ---
# This call now happens AFTER the sidebar code.
model = get_generative_model(st.session_state.system_prompt_for_chat)

if not model:
    st.error("Failed to load/initialize the generative model. Application cannot proceed.")
    # The error from get_generative_model itself should have already been displayed.
    st.stop() # Halts script execution if model loading fails

# --- Chat Session Initialization ---
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])
    # Initialize messages only if chat session is new AND messages are not already populated
    # (e.g. by a prompt change reset)
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
    with st.chat_message(message["role"]): 
        st.markdown(message["content"])

# --- Getting User Input and Processing It ---
if user_prompt := st.chat_input("Type your question here..."):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"): 
        st.markdown(user_prompt)

    if "chat_session" in st.session_state: 
        try:
            chat_session_to_use = st.session_state.chat_session
            model_response = chat_session_to_use.send_message(user_prompt)
            response_text = model_response.text

            st.session_state.messages.append({"role": "assistant", "content": response_text})
            with st.chat_message("assistant"): 
                st.markdown(response_text)

        except Exception as e:
            error_for_display = f"Oops, an error occurred while communicating with the model: {e}"
            st.session_state.messages.append({"role": "assistant", "content": error_for_display})
            with st.chat_message("assistant"): 
                st.error(error_for_display)
            st.toast(f"Error: {e}")
    else:
        st.error("Chat session is not initialized. Please ensure the model and system prompt are correctly configured.")

