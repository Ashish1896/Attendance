import streamlit as st
from PIL import Image


@st.dialog("Capture or upload photos")
def add_photos_dialog():

    st.write('Add classroom photos to scan for attendance')

    if 'photo_tab' not in st.session_state:
        st.session_state.photo_tab = 'camera'

    t1, t2 = st.columns(2)

    with t1:
        type_camera = "primary" if st.session_state.photo_tab == 'camera' else 'tertiary'
        if st.button('Camera', type=type_camera, width='stretch', key='phototab_cam'):
            st.session_state.photo_tab = 'camera'
            st.rerun()

    with t2:
        type_upload = "primary" if st.session_state.photo_tab == 'upload' else 'tertiary'
        if st.button('Upload photos', type=type_upload, width='stretch', key='phototab_upload'):
            st.session_state.photo_tab = 'upload'
            st.rerun()

    if st.session_state.photo_tab == 'camera':
        cam_photo = st.camera_input('Take Snapshot', key='dialog_cam')
        if cam_photo:
            photo_bytes = cam_photo.getvalue()
            # Dedup by checking against last captured camera photo bytes
            if photo_bytes != st.session_state.get('last_cam_bytes'):
                st.session_state.last_cam_bytes = photo_bytes
                img = Image.open(cam_photo).convert('RGB')
                st.session_state.attendance_images.append(img)
                st.toast(f'Photo Captured! ({len(st.session_state.attendance_images)} total)')

    if st.session_state.photo_tab == 'upload':
        uploaded_files = st.file_uploader(
            'Choose image files',
            type=['jpg', 'png', 'jpeg'],
            accept_multiple_files=True,
            key='dialog_upload'
        )

        if uploaded_files:
            if 'processed_upload_keys' not in st.session_state:
                st.session_state.processed_upload_keys = set()

            added = 0
            for f in uploaded_files:
                file_key = f"{f.name}_{f.size}"
                if file_key not in st.session_state.processed_upload_keys:
                    try:
                        img = Image.open(f).convert('RGB')
                        st.session_state.attendance_images.append(img)
                        st.session_state.processed_upload_keys.add(file_key)
                        added += 1
                    except Exception:
                        st.error(f"Invalid image file: {f.name}")

            if added:
                st.success(f'✅ {added} new photo(s) added!')

    st.divider()

    count = len(st.session_state.get('attendance_images', []))
    if count > 0:
        st.info(f"📸 Total photos added: {count}")

    if st.button('Done', type='primary', width='stretch', key='photo_done'):
        # Reset tracking and close dialog
        st.session_state.pop('last_cam_bytes', None)
        st.session_state.pop('processed_upload_keys', None)
        st.session_state.show_add_photos_dialog = False
        st.rerun()