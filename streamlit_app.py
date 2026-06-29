import streamlit as st
import requests

BASE_URL = st.sidebar.text_input("FastAPI base URL", value="http://127.0.0.1:8000")

st.set_page_config(page_title="Patient Health Assistant Agent", layout="wide")
st.title("Patient Management System")

page = st.sidebar.radio(
    "Go to",
    ["View All", "View Single Patient", "Sort Patients", "Create Patient",
     "Update Patient", "Delete Patient", "Symptom Checker"]
)


def get(path, params=None):
    try:
        r = requests.get(f"{BASE_URL}{path}", params=params, timeout=15)
        return r
    except requests.exceptions.ConnectionError:
        st.error(f"Can't reach {BASE_URL}. Is the FastAPI server running?")
        return None


def post(path, json_body):
    try:
        r = requests.post(f"{BASE_URL}{path}", json=json_body, timeout=30)
        return r
    except requests.exceptions.ConnectionError:
        st.error(f"Can't reach {BASE_URL}. Is the FastAPI server running?")
        return None


def put(path, json_body):
    try:
        r = requests.put(f"{BASE_URL}{path}", json=json_body, timeout=15)
        return r
    except requests.exceptions.ConnectionError:
        st.error(f"Can't reach {BASE_URL}. Is the FastAPI server running?")
        return None


def delete(path):
    try:
        r = requests.delete(f"{BASE_URL}{path}", timeout=15)
        return r
    except requests.exceptions.ConnectionError:
        st.error(f"Can't reach {BASE_URL}. Is the FastAPI server running?")
        return None


if page == "View All":
    st.header("All Patients")
    if st.button("Refresh"):
        st.rerun()
    r = get("/view")
    if r is not None:
        if r.status_code == 200:
            data = r.json()
            if not data:
                st.info("No patients in the database.")
            else:
                st.dataframe(
                    [{"id": pid, **info} for pid, info in data.items()],
                    use_container_width=True
                )
        else:
            st.error(f"Request failed: {r.status_code} - {r.text}")


elif page == "View Single Patient":
    st.header("Look Up a Patient")
    patient_id = st.text_input("Patient ID", placeholder="P001")
    if st.button("Search") and patient_id:
        r = get(f"/patient/{patient_id}")
        if r is not None:
            if r.status_code == 200:
                st.json(r.json())
            elif r.status_code == 404:
                st.error("Patient not found.")
            else:
                st.error(f"Request failed: {r.status_code} - {r.text}")


elif page == "Sort Patients":
    st.header("Sort Patients")
    col1, col2 = st.columns(2)
    with col1:
        sort_by = st.selectbox("Sort by", ["height", "weight", "bmi"])
    with col2:
        order = st.selectbox("Order", ["asc", "desc"])

    if st.button("Sort"):
        r = get("/sort", params={"sort_by": sort_by, "order": order})
        if r is not None:
            if r.status_code == 200:
                st.dataframe(r.json(), use_container_width=True)
            else:
                st.error(f"Request failed: {r.status_code} - {r.text}")


elif page == "Create Patient":
    st.header("Create a New Patient")
    with st.form("create_form"):
        pid = st.text_input("ID", placeholder="P1001")
        name = st.text_input("Name")
        city = st.text_input("City")
        age = st.number_input("Age", min_value=1, max_value=120, value=30)
        gender = st.selectbox("Gender", ["male", "female", "others"])
        height = st.number_input("Height (m)", min_value=0.1, max_value=3.0, value=1.7, format="%.2f")
        weight = st.number_input("Weight (kg)", min_value=0.1, max_value=400.0, value=70.0, format="%.1f")
        allergy_raw = st.text_input("Allergies (comma separated, optional)")
        submitted = st.form_submit_button("Create")

    if submitted:
        if not pid or not name or not city:
            st.error("ID, name, and city are required.")
        else:
            allergy_list = [a.strip() for a in allergy_raw.split(",") if a.strip()] or None
            payload = {
                "id": pid, "name": name, "city": city, "age": age,
                "gender": gender, "height": height, "weight": weight,
                "allergy": allergy_list
            }
            r = post("/create", payload)
            if r is not None:
                if r.status_code == 201:
                    st.success("Patient created.")
                elif r.status_code == 400:
                    st.error(r.json().get("detail", "Patient already exists."))
                else:
                    st.error(f"Request failed: {r.status_code} - {r.text}")


elif page == "Update Patient":
    st.header("Update an Existing Patient")
    patient_id = st.text_input("Patient ID to update", placeholder="P1001")
    st.caption("Leave a field blank to keep it unchanged.")

    with st.form("update_form"):
        name = st.text_input("Name (optional)")
        city = st.text_input("City (optional)")
        age = st.text_input("Age (optional, number)")
        gender = st.selectbox("Gender (optional)", ["", "male", "female", "others"])
        height = st.text_input("Height in meters (optional, number)")
        weight = st.text_input("Weight in kg (optional, number)")
        submitted = st.form_submit_button("Update")

    if submitted:
        if not patient_id:
            st.error("Patient ID is required.")
        else:
            payload = {}
            if name:
                payload["name"] = name
            if city:
                payload["city"] = city
            if age:
                try:
                    payload["age"] = int(age)
                except ValueError:
                    st.error("Age must be a whole number.")
                    st.stop()
            if gender:
                payload["gender"] = gender
            if height:
                try:
                    payload["height"] = float(height)
                except ValueError:
                    st.error("Height must be a number.")
                    st.stop()
            if weight:
                try:
                    payload["weight"] = float(weight)
                except ValueError:
                    st.error("Weight must be a number.")
                    st.stop()

            if not payload:
                st.warning("Nothing to update, you left every field blank.")
            else:
                r = put(f"/edit/{patient_id}", payload)
                if r is not None:
                    if r.status_code == 200:
                        st.success("Patient updated.")
                    elif r.status_code == 404:
                        st.error("Patient not found.")
                    else:
                        st.error(f"Request failed: {r.status_code} - {r.text}")


elif page == "Delete Patient":
    st.header("Delete a Patient")
    patient_id = st.text_input("Patient ID to delete", placeholder="P1001")
    confirm = st.checkbox("I understand this is permanent.")
    if st.button("Delete", type="primary", disabled=not confirm):
        r = delete(f"/delete/{patient_id}")
        if r is not None:
            if r.status_code == 200:
                st.success("Patient deleted.")
            elif r.status_code == 404:
                st.error("Patient not found.")
            else:
                st.error(f"Request failed: {r.status_code} - {r.text}")


elif page == "Symptom Checker":
    st.header("Symptom Checker")
    patient_id = st.text_input("Patient ID", placeholder="P1001")
    symptoms = st.text_area("Symptoms", placeholder="fever, headache, fatigue")

    if st.button("Analyze") and patient_id and symptoms:
        with st.spinner("Running search and asking the model..."):
            r = post("/chat", {"id": patient_id, "symptoms": symptoms})
        if r is not None:
            if r.status_code == 200:
                result = r.json()
                risk = result.get("risk_level", "Unknown")
                color = {"High": "red", "Medium": "orange", "Low": "green"}.get(risk, "gray")
                st.markdown(f"**Risk level:** :{color}[{risk}]")
                st.markdown(f"**Possible cause:** {result.get('possible_cause', '-')}")
                st.markdown(f"**Recommendation:** {result.get('recommendation', '-')}")
                st.markdown(f"**Summary:** {result.get('summary', '-')}")
                sources = result.get("source", [])
                if sources:
                    st.markdown("**Sources:**")
                    for s in sources:
                        st.markdown(f"- {s}")
            elif r.status_code == 400:
                st.error(r.json().get("detail", "Patient not found."))
            else:
                st.error(f"Request failed: {r.status_code} - {r.text}")