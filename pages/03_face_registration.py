"""
pages/03_face_registration.py
==============================
Face Registration — No login required.
"""

import streamlit as st
from PIL import Image

from utils.ui_helpers         import setup_page, render_sidebar_brand, page_title, section_header, empty_state, inject_css
from utils.constants          import MIN_FACE_IMAGES, MAX_FACE_IMAGES
from services.attendance_service import get_all_students
from services.face_service    import get_average_encoding, save_face_embedding, detect_faces, draw_face_boxes, bytes_to_image


setup_page("Face Registration", "🧠")
inject_css()
render_sidebar_brand()

page_title("Face Registration", "Upload student face images to train the recognition model", "🧠")
st.markdown("---")

students = get_all_students()
if not students:
    empty_state("👤", "No Students", "Add students first before registering faces.")
    st.stop()

student_map = {s["id"]: f"{s['name']} ({s['roll_number']})" for s in students}

col_sel, col_info = st.columns([2, 1])
with col_sel:
    selected_id = st.selectbox("Select Student", options=list(student_map.keys()),
                                format_func=lambda sid: student_map.get(sid, sid), key="face_reg_student")
selected_student = next((s for s in students if s["id"] == selected_id), None)

if selected_student:
    with col_info:
        fi = selected_student.get("face_images", 0) or 0
        st.metric("Registered Images", fi, delta="✅ Ready" if fi >= 3 else "⚠️ Needs 3+")

st.markdown("---")
section_header("Upload Face Images", f"{MIN_FACE_IMAGES}–{MAX_FACE_IMAGES} photos required")
st.info(f"📸 Upload {MIN_FACE_IMAGES}–{MAX_FACE_IMAGES} clear face photos. Good lighting, face camera directly. No glasses/masks.")

uploaded_files = st.file_uploader("Choose face images", type=["jpg","jpeg","png","webp"],
                                   accept_multiple_files=True, key="face_images_uploader")

if uploaded_files:
    count = len(uploaded_files)
    if count < MIN_FACE_IMAGES:
        st.warning(f"⚠️ Need at least {MIN_FACE_IMAGES} images. Uploaded {count}.")
    elif count > MAX_FACE_IMAGES:
        st.error(f"❌ Max {MAX_FACE_IMAGES} images. Trimming to first {MAX_FACE_IMAGES}.")
        uploaded_files = uploaded_files[:MAX_FACE_IMAGES]
    else:
        st.success(f"✅ {count} image(s) ready. Detecting faces…")

    valid_images, invalid_images = [], []
    num_cols = min(count, 5)
    preview_cols = st.columns(num_cols)
    progress_bar = st.progress(0, text="Analyzing…")

    for i, f in enumerate(uploaded_files):
        img_bytes = f.read()
        pil_img   = bytes_to_image(img_bytes)
        faces     = detect_faces(pil_img)
        annotated = draw_face_boxes(pil_img, faces)
        preview_cols[i % num_cols].image(annotated,
            caption=f"{'✅' if faces else '❌'} {f.name[:15]}", use_container_width=True)
        (valid_images if faces else invalid_images).append(pil_img if faces else f.name)
        progress_bar.progress((i+1)/len(uploaded_files), text=f"Processing {i+1}/{count}…")

    progress_bar.empty()

    c1, c2, c3 = st.columns(3)
    c1.metric("Uploaded", count)
    c2.metric("✅ Faces Found", len(valid_images))
    c3.metric("❌ No Face", len(invalid_images))

    if invalid_images:
        st.warning(f"No face in: {', '.join(str(x) for x in invalid_images)}")

    st.markdown("---")
    ready = len(valid_images) >= MIN_FACE_IMAGES

    if not ready:
        st.error(f"❌ Need {MIN_FACE_IMAGES}+ images with faces. Found {len(valid_images)}.")
    else:
        st.success(f"✅ Ready! {len(valid_images)} valid face images.")
        if st.button(f"🧠 Generate & Save Embedding ({len(valid_images)} images)", use_container_width=True):
            with st.spinner("Computing face embeddings… (takes a few seconds)"):
                avg_embedding = get_average_encoding(valid_images)
            if avg_embedding is None:
                st.error("❌ Could not generate embeddings. Ensure faces are clearly visible.")
            else:
                ok = save_face_embedding(selected_id, avg_embedding, len(valid_images))
                if ok:
                    st.success(f"✅ Embedding saved for **{selected_student['name']}**!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Failed to save to database.")

st.markdown("---")
section_header("Registration Status")
import pandas as pd
reg_df = pd.DataFrame([{
    "Name": s["name"], "Roll No": s["roll_number"], "Department": s["department"],
    "Face Images": s.get("face_images", 0) or 0,
    "Status": "✅ Registered" if (s.get("face_images") or 0) >= MIN_FACE_IMAGES else "⚠️ Pending"
} for s in students])
st.dataframe(reg_df, use_container_width=True, hide_index=True)
