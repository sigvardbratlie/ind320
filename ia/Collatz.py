import streamlit as st
import random

# This is a solution to the Collatz conjecture exercise with the bonus that it stops at 1 and shows balloons.

st.title("Collatz conjecture")

# Initialize session state
if "value" not in st.session_state:
    st.session_state.value = None
    st.session_state.started = False
    st.session_state.count = 0
    st.session_state.stopped = False
    button_label = "Start"
else:
    if st.session_state.value == 1:
        button_label = "Success!"
    else:
        if st.session_state.stopped:
            button_label = "Stopped"
        st.session_state.count += 1
        if st.session_state.count >= 20:
            @st.dialog("Continue?")
            def continue_or_not():
                st.write("Do you want to continue?")
                if st.button("Yes"):
                    st.write("Continuing...")
                    st.session_state.count = 0
                if st.button("No"):
                    st.write("Stopping...")
                    st.session_state.count = 0
                    st.session_state.stopped = True
                st.rerun()


            continue_or_not()
        if st.session_state.value % 2 == 0:
            button_label = "Half it"
        else:
            button_label = "Triple and add one"

# Button label depends on state
st.button(button_label, disabled=st.session_state.value == 1 or st.session_state.stopped)
if st.session_state.value == 1:
    st.balloons()

# Output
if not st.session_state.started:
    st.write("Ready")
else:
    st.write(f'Value : {st.session_state.value} | Count : {st.session_state.count}')

if not st.session_state.started:
    # First press: sample random integer and cache it
    st.session_state.value = random.randint(1, 100)
    st.session_state.started = True
else:
    # Subsequent presses: apply Collatz update
    if st.session_state.value % 2 == 0:
        st.session_state.value //= 2
    else:
        st.session_state.value = st.session_state.value * 3 + 1

