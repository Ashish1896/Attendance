"""
pages/04_face_attendance.py
============================
Face Attendance — Webcam capture + OpenCV recognition. No login required.
"""

import streamlit as st
import pandas as pd
from PIL import Image
from datetime import date

from utils.ui_helpers         import setup_page, render_sidebar_brand, page_title, section_header, empty_state, inject_css
from utils.constants          import FACE_MATCH_THRESHOLD
from services.face_service    import get_face_encoding, match_face_in_db, draw_face_boxes, detect_faces
from services.attendance_service import mark_attendance, get_today_attendance


setup_page("Face Attendance", "📷")
inject_css()
render_sidebar_brand()

page_title("Face Attendance", "Capture your face to mark attendance automatically", "📷")
st.markdown("---")

st.info("📸 Look directly at the camera with good lighting, then click **Take Photo**. Your attendance is marked automatically.")

col_cam, col_result = st.columns([3, 2])

with col_cam:
    section_header("Camera Capture")
    img_file = st.camera_input("📷 Click to capture", key="attendance_camera")

with col_result:
    section_header("Recognition Result")

    if not img_file:
        empty_state("🤖", "Waiting for Photo", "Take a photo to start recognition")
    else:
        with st.spinner("🔍 Detecting and matching face…"):
            try:
                pil_img = Image.open(img_file).convert("RGB")
                faces   = detect_faces(pil_img)

                if not faces:
                    st.error("❌ No face detected.")
                    st.markdown("**Tips:** Good lighting · Face the camera · Remove glasses")
                else:
                    annotated = draw_face_boxes(pil_img, faces)
                    col_cam.image(annotated, caption=f"✅ {len(faces)} face(s) detected", use_container_width=True)

                    encoding = get_face_encoding(pil_img)
                    if encoding is None:
                        st.error("❌ Could not generate face encoding. Try again.")
                    else:
                        match = match_face_in_db(encoding, FACE_MATCH_THRESHOLD)

                        if match is None:
                            st.error("❌ **Face Not Recognized**")
                            st.markdown("Student not registered or poor image quality.")
                        else:
                            confidence = match.get("confidence", 0)
                            name       = match.get("name", "Unknown")
                            roll       = match.get("roll_number", "")
                            dept       = match.get("department", "")
                            student_id = match.get("student_id", "")

                            st.success(f"✅ **Recognized: {name}**")
                            st.markdown(f"""
| | |
|---|---|
| 👤 Name | **{name}** |
| 🆔 Roll | {roll} |
| 🏫 Dept | {dept} |
| 🎯 Confidence | {confidence*100:.1f}% |
""")
                            st.progress(min(int(confidence * 100), 100) / 100)
                            st.markdown("<br>", unsafe_allow_html=True)

                            if st.button("✅ Mark Attendance", key="mark_btn",
                                         use_container_width=True, type="primary"):
                                ok, msg = mark_attendance(
                                    student_id=student_id, method="face",
                                    status="present", confidence=confidence,
                                )
                                if ok:
                                    st.success(f"🎉 {msg}")
                                    st.balloons()
                                else:
                                    st.warning(f"⚠️ {msg}")
            except Exception as exc:
                st.error(f"❌ Error: {exc}")

st.markdown("---")
section_header("Today's Face Attendance", date.today().strftime("%d %b %Y"))
records = [r for r in get_today_attendance() if r.get("method") == "face"]
if records:
    df = pd.DataFrame(records)
    cols = [c for c in ["student_name","roll_number","department","time","status"] if c in df.columns]
    show = df[cols].rename(columns={"student_name":"Student","roll_number":"Roll No",
                                     "department":"Department","time":"Time","status":"Status"})
    if "Status" in show.columns:
        show["Status"] = show["Status"].map({"present":"✅ Present","absent":"❌ Absent","late":"⏰ Late"}).fillna(show["Status"])
    st.dataframe(show, use_container_width=True, hide_index=True)
    st.caption(f"📷 {len(records)} face records today")
else:
    empty_state("📷", "No Face Attendance Today", "Records appear after face recognition.")
