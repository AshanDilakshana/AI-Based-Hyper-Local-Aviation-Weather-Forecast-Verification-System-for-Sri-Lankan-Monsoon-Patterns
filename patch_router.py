import re

with open('backend/api/routers/cloud_visibility_router.py', 'r') as f:
    content = f.read()

content = content.replace(
"""cloud_model = None
cloud_mapping = None""",
"""cloud_model = None
cloud_mapping = None
cloud_type_model = None
cloud_height_model = None
cloud_type_mapping = None"""
)

content = content.replace(
"""    global cloud_model, cloud_mapping, vis_model, vis_mapping""",
"""    global cloud_model, cloud_mapping, cloud_type_model, cloud_height_model, cloud_type_mapping, vis_model, vis_mapping"""
)

# Replace primary load
content = content.replace(
"""            with open(cloud_primary, "rb") as f:
                cloud_bundle = pickle.load(f)
            cloud_model = cloud_bundle["model"]
            cloud_mapping = cloud_bundle["mapping"]
            print("[SUCCESS] Loaded Primary Cloud XGBoost Model.")""",
"""            with open(cloud_primary, "rb") as f:
                cloud_bundle = pickle.load(f)
            if 'type_model' in cloud_bundle:
                cloud_type_model = cloud_bundle['type_model']
                cloud_height_model = cloud_bundle['height_model']
                cloud_type_mapping = cloud_bundle['type_mapping']
            else:
                cloud_model = cloud_bundle["model"]
                cloud_mapping = cloud_bundle["mapping"]
            print("[SUCCESS] Loaded Primary Cloud XGBoost Model.")"""
)

# Replace backup load
content = content.replace(
"""                with open(cloud_backup, "rb") as f:
                    cloud_bundle = pickle.load(f)
                cloud_model = cloud_bundle["model"]
                cloud_mapping = cloud_bundle["mapping"]
                print("[SUCCESS] Loaded Backup Cloud XGBoost Model.")""",
"""                with open(cloud_backup, "rb") as f:
                    cloud_bundle = pickle.load(f)
                if 'type_model' in cloud_bundle:
                    cloud_type_model = cloud_bundle['type_model']
                    cloud_height_model = cloud_bundle['height_model']
                    cloud_type_mapping = cloud_bundle['type_mapping']
                else:
                    cloud_model = cloud_bundle["model"]
                    cloud_mapping = cloud_bundle["mapping"]
                print("[SUCCESS] Loaded Backup Cloud XGBoost Model.")"""
)

content = content.replace(
"""    if cloud_model is None or vis_model is None:""",
"""    if (cloud_model is None and cloud_type_model is None) or vis_model is None:"""
)

content = content.replace(
"""        # =================================================
        # CLOUD PREDICTION
        # =================================================

        cloud_raw_pred = cloud_model.predict(input_data)[0]

        cloud_idx = int(np.clip(np.round(cloud_raw_pred), 0, len(cloud_mapping) - 1))""",
"""        # =================================================
        # CLOUD PREDICTION
        # =================================================

        if cloud_type_model is not None and cloud_height_model is not None:
            type_raw = cloud_type_model.predict(input_data)[0]
            type_idx = int(np.clip(np.round(type_raw), 0, len(cloud_type_mapping) - 1))
            cloud_type = str(cloud_type_mapping[type_idx])
            
            height_raw = cloud_height_model.predict(input_data)[0]
            cloud_height = int(np.clip(np.round(height_raw), 0, 999))
            
            if cloud_type in ['NSC', 'SKC', 'CLR', 'CAVOK', 'NIL']:
                cloud_status = cloud_type
            else:
                cloud_status = f"{cloud_type}{cloud_height:03d}"
        else:
            cloud_raw_pred = cloud_model.predict(input_data)[0]
            cloud_idx = int(np.clip(np.round(cloud_raw_pred), 0, len(cloud_mapping) - 1))
            cloud_status = str(cloud_mapping[cloud_idx])"""
)

content = content.replace(
"""            unified_record.clouds = str(cloud_mapping[cloud_idx])""",
"""            unified_record.clouds = cloud_status"""
)

content = content.replace(
"""        return CloudVisibilityResponse(
            visibility_prediction=int(float(vis_mapping[vis_idx])),
            cloud_status=str(cloud_mapping[cloud_idx]),
        )""",
"""        return CloudVisibilityResponse(
            visibility_prediction=int(float(vis_mapping[vis_idx])),
            cloud_status=cloud_status,
        )"""
)

with open('backend/api/routers/cloud_visibility_router.py', 'w') as f:
    f.write(content)
