
import streamlit as st

# 1. Set page config (always good to have, must be first st command)
st.set_page_config(page_title="Sidebar Test App", page_icon="🧪")

# 2. Try to add elements to the sidebar
st.sidebar.header("Test Sidebar Header")
st.sidebar.markdown("If you see this, the sidebar header was created.")

user_text = st.sidebar.text_area("Test Text Area:", "You can type here...")

if st.sidebar.button("Test Button"):
    st.sidebar.write(f"Button clicked! Text area content: {user_text}")

st.sidebar.markdown("---") # A separator
st.sidebar.markdown("End of sidebar test elements.")

# 3. Add something to the main page so we know it's running
st.title("Main Page Title - Sidebar Test")
st.write("This is the main content area of the application.")
st.write("Please check the sidebar (usually on the left, might need to be expanded with a '>' icon) to see if the test elements appear.")
