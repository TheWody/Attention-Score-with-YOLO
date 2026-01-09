import numpy as np

class AttentionAnalyzer:

    def __init__(self):
        self.POSE_WEIGHT = 0.6
        self.EMOTION_WEIGHT = 0.4

        self.HEAD_DOWN_NORM_THRESHOLD = 0.15
        self.HEAD_DOWN_THRESHOLD = 50

    def analyze_head_pose(self, keypoints):
        NOSE = 0
        L_SHOULDER = 5
        R_SHOULDER = 6
        L_HIP = 11
        R_HIP = 12

        if keypoints.shape[0] < 13:
            return "UNKNOWN"

        try:
            nose = keypoints[NOSE]
            l_shoulder = keypoints[L_SHOULDER]
            r_shoulder = keypoints[R_SHOULDER]
            l_hip = keypoints[L_HIP]
            r_hip = keypoints[R_HIP]

            avg_hip_y = (r_hip[1] + l_hip[1]) / 2.0
            avg_shoulder_y = (r_shoulder[1] + l_shoulder[1]) / 2.0

            body_height = avg_hip_y - avg_shoulder_y

            y_diff = nose[1] - avg_shoulder_y

            if body_height > 10:
                normalized_diff = y_diff / body_height
            else:
                normalized_diff = 0

            if normalized_diff > self.HEAD_DOWN_NORM_THRESHOLD:

                return "DISTRACTED"
            else:
                return "ATTENTIVE"

        except IndexError:
            return "UNKNOWN"

    def calculate_attention_score(self, pose_state, emotion_label="neutral"):

        pose_score = 0
        if pose_state == "ATTENTIVE":
            pose_score = 100
        elif pose_state == "DISTRACTED":
            pose_score = 20
        else:
            pose_score = 50

        emotion_score = 0

        attentive_emotions = ["happy", "neutral", "surprised"]

        distracted_emotions = ["sad", "angry", "bored"]

        if emotion_label in attentive_emotions:
            emotion_score = 100
        elif emotion_label in distracted_emotions:
            emotion_score = 40
        else:
            emotion_score = 70

        final_score = (pose_score * self.POSE_WEIGHT) + (emotion_score * self.EMOTION_WEIGHT)

        return max(0, min(100, int(final_score)))